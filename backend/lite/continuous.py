import math
import numpy.random as npr
import numpy as np
import stats_utils as su
from utils import override, numpy_force_number, logDensityNormal, logDensityMVNormal, MVNormalRnd
from exception import VentureValueError, GradientWarning
import warnings

# For some reason, pylint can never find numpy members (presumably metaprogramming).
# pylint: disable=no-member

from psp import RandomPSP
from lkernel import LKernel

class MVDNormalRandomWalkKernel(LKernel):
  def __init__(self,epsilon = 0.7):
    self.epsilon = epsilon if epsilon is not None else 0.7

  def simulate(self,trace,oldValue,args):
    (mu, _) = MVDNormalOutputPSP.__parse_args__(args)
    nu = npr.normal(0,self.epsilon,mu.shape)
    return oldValue + nu

  @override(LKernel)
  def weight(self, _trace, _newValue, _oldValue, _args):
    # log P(_newValue --> _oldValue) == log P(_oldValue --> _newValue)
    return MVDNormalOutputPSP.logDensity(_newValue, _args)

class MVDNormalOutputPSP(RandomPSP):
  def simulate(self, args):
    (mu, sigma) = self.__parse_args__(args)
    return mu + npr.normal(size = mu.shape) * sigma

  @staticmethod
  def logDensity(x, args):
    (mu, sigma) = MVDNormalOutputPSP.__parse_args__(args)
    return sum(logDensityNormal(x, mu, sigma))

  def hasDeltaKernel(self): return True
  def getDeltaKernel(self,*args): return MVDNormalRandomWalkKernel(*args)

  def description(self,name):
    return "  (%s mean covariance) samples a vector according to the given multivariate Gaussian distribution with a diagonal covariance matrix.  It is an error if the dimensionalities of the arguments do not line up." % name

  @staticmethod
  def __parse_args__(args):
    return (np.array(args.operandValues[0]), np.array(args.operandValues[1]))

class MVNormalRandomWalkKernel(LKernel):
  def __init__(self,epsilon = 0.7):
    self.epsilon = epsilon if epsilon is not None else 0.7

  def simulate(self,trace,oldValue,args):
    (mu, _) = MVNormalOutputPSP.__parse_args__(args)
    nu = npr.normal(0,self.epsilon,mu.shape)
    return oldValue + nu

  @override(LKernel)
  def weight(self, _trace, _newValue, _oldValue, _args):
    # log P(_newValue --> _oldValue) == log P(_oldValue --> _newValue)
    return MVNormalOutputPSP.logDensity(_newValue, _args)

class MVNormalOutputPSP(RandomPSP):
  def simulate(self, args):
    return MVNormalRnd(*self.__parse_args__(args))

  @staticmethod
  def logDensity(x, args):
    (mu, sigma) = MVNormalOutputPSP.__parse_args__(args)
    return logDensityMVNormal(x, mu, sigma)

  def hasDeltaKernel(self): return True
  def getDeltaKernel(self,*args): return MVNormalRandomWalkKernel(*args)

  def description(self,name):
    return "  (%s mean covariance) samples a vector according to the given multivariate Gaussian distribution.  It is an error if the dimensionalities of the arguments do not line up." % name

  @staticmethod
  def __parse_args__(args):
    return (np.array(args.operandValues[0]), np.array(args.operandValues[1]))

class NormalOutputPSP(RandomPSP):
  # TODO don't need to be class methods
  def simulateNumeric(self,params): return npr.normal(*params)
  def logDensityNumeric(self,x,params):
    mu, sigma = params
    return numpy_force_number(logDensityNormal(x, mu, sigma))
  def logDensityBoundNumeric(self, x, mu, sigma):
    if sigma is not None:
      return -(math.log(sigma) + 0.5 * math.log(2 * math.pi))
    elif x is not None and mu is not None:
      # Per the derivative of the log density noted in the
      # gradientOfLogDensity method, the maximum occurs when
      # (x-mu)^2 = sigma^2
      # normal_logpdf(x, mu, abs(x-mu))
      return -0.5 - 0.5 * math.log(2 * math.pi * (x - mu)**2)
    else:
      raise Exception("Cannot rejection sample psp with unbounded likelihood")

  def simulate(self,args): return self.simulateNumeric(args.operandValues)
  def gradientOfSimulate(self, args, value, direction):
    # Reverse engineering the behavior of scipy.stats.norm.rvs
    # suggests this gradient is correct.
    (mu, sigma) = args.operandValues
    deviation = (value - mu) / sigma
    return [direction*1, direction*deviation]
  def logDensity(self,x,args): return self.logDensityNumeric(x,args.operandValues)
  def logDensityBound(self, x, args): return self.logDensityBoundNumeric(x, *args.operandValues)

  def hasDeltaKernel(self): return False # have each gkernel control whether it is delta or not
  def getDeltaKernel(self,args): return NormalDriftKernel(args)

  def hasVariationalLKernel(self): return True
  def getParameterScopes(self): return ["REAL","POSITIVE_REAL"]

  def gradientOfLogDensity(self,x,args):
    mu = args.operandValues[0]
    sigma = args.operandValues[1]

    gradX = -(x - mu) / (math.pow(sigma,2))
    gradMu = (x - mu) / (math.pow(sigma,2))
    gradSigma = (math.pow(x - mu,2) - math.pow(sigma,2)) / math.pow(sigma,3)
    # for positive sigma, d(log density)/d(sigma) is <=> zero
    # when math.pow(x - mu,2) <=> math.pow(sigma,2) respectively
    return (gradX,[gradMu,gradSigma])

  def description(self,name):
    return "  (%s mu sigma) samples a normal distribution with mean mu and standard deviation sigma." % name

class UniformOutputPSP(RandomPSP):
  # TODO don't need to be class methods
  def simulateNumeric(self,low,high): return npr.uniform(low, high)
  def logDensityNumeric(self,x,low,high): return -math.log(high - low)
  def logDensityBoundNumeric(self, _, low, high):
    if low is None or high is None:
      # Unbounded
      raise Exception("Cannot rejection sample psp with unbounded likelihood")
    else:
      return -math.log(high - low)

  def simulate(self,args): return self.simulateNumeric(*args.operandValues)
  def logDensity(self,x,args): return self.logDensityNumeric(x,*args.operandValues)
  def gradientOfLogDensity(self, _, args):
    spread = 1.0/(args.operandValues[1]-args.operandValues[0])
    return (0, [spread, -spread])
  def logDensityBound(self, x, args): return self.logDensityBoundNumeric(x, *args.operandValues)

  def description(self,name):
    return "  (%s low high) -> samples a uniform real number between low and high." % name

  # TODO Uniform presumably has a variational kernel?

class GammaOutputPSP(RandomPSP):
  # TODO don't need to be class methods
  def simulateNumeric(self,alpha,beta): return npr.gamma(alpha,scale=1.0/beta)
  def logDensityNumeric(self,x,alpha,beta):
    return -su.C.gammaln(alpha) + alpha * math.log(beta) + (alpha - 1) * math.log(x) - x * beta

  def simulate(self,args): return self.simulateNumeric(*args.operandValues)
  def logDensity(self,x,args): return self.logDensityNumeric(x,*args.operandValues)

  def description(self,name):
    return "  (%s alpha beta) returns a sample from a gamma distribution with shape parameter alpha and rate parameter beta." % name

