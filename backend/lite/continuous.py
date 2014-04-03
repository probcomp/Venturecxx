import numbers
import scipy.stats
import scipy.special
import math
import numpy.random as npr
import numpy.linalg as npla
import numpy as np
from utils import logDensityMVNormal

# For some reason, pylint can never find numpy members (presumably metaprogramming).
# pylint: disable=no-member

from psp import RandomPSP
from lkernel import LKernel

class NormalDriftKernel(LKernel):
  def __init__(self,epsilon = 0.7): self.epsilon = epsilon

  def simulate(self,trace,oldValue,args):
    mu,sigma = args.operandValues
    nu = scipy.stats.norm.rvs(0,sigma)
    term1 = mu
    term2 = math.sqrt(1 - (self.epsilon * self.epsilon)) * (oldValue - mu)
    term3 = self.epsilon * nu
    return term1 + term2 + term3
                                                        
class MVNormalOutputPSP(RandomPSP):
  def simulate(self, args):
    return npr.multivariate_normal(*self.__parse_args__(args))

  def logDensity(self, x, args):
    (mu, sigma) = self.__parse_args__(args)
    return logDensityMVNormal(x, mu, sigma)

  def gradientOfLogDensity(self, x, args):
    (mu, sigma) = (np.array(args[0]), args[1])
    isigma = npla.inv(sigma)
    xvar = np.dot(x-mu, np.transpose(x-mu))
    gradX = -np.dot(isigma, np.transpose(x-mu))
    gradMu = np.dot(isigma, np.transpose(x-mu))
    gradSigma = .5*np.dot(np.dot(isigma, xvar),isigma)-.5*isigma
    return np.array(gradX)[0].tolist(), [np.array(gradMu)[0].tolist(), gradSigma]

  def description(self,name):
    return "  (%s mean covariance) samples a vector according to the given multivariate Gaussian distribution.  It is an error if the dimensionalities of the arguments do not line up." % name

  def __parse_args__(self, args):
    return (np.array(args.operandValues[0]), args.operandValues[1])

class NormalOutputPSP(RandomPSP):
  # TODO don't need to be class methods
  def simulateNumeric(self,params): return scipy.stats.norm.rvs(*params)
  def logDensityNumeric(self,x,params): return scipy.stats.norm.logpdf(x,*params)
  def logDensityBoundNumeric(self, x, mu, sigma):
    if sigma is not None:
      return -(math.log(sigma) + 0.5 * math.log(2 * math.pi))
    elif x is not None and mu is not None:
      # Per the derivative of the log density noted in the
      # gradientOfLogDensity method, the maximum occurs when
      # (x-mu)^2 = sigma^2
      return scipy.stats.norm.logpdf(x, mu, abs(x-mu))
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
  def getDeltaKernel(self): return NormalDriftKernel()

  def hasVariationalLKernel(self): return True
  def getParameterScopes(self): return ["REAL","POSITIVE_REAL"]

  def gradientOfLogDensity(self,x,params):
    mu = params[0]
    sigma = params[1]

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
  def simulateNumeric(self,low,high): return scipy.stats.uniform.rvs(low, high-low)
  def logDensityNumeric(self,x,low,high): return scipy.stats.uniform.logpdf(x, low, high-low)
  def logDensityBoundNumeric(self, _, low, high):
    if low is None or high is None:
      # Unbounded
      raise Exception("Cannot rejection sample psp with unbounded likelihood")
    else:
      return -math.log(high - low)

  def simulate(self,args): return self.simulateNumeric(*args.operandValues)
  def logDensity(self,x,args): return self.logDensityNumeric(x,*args.operandValues)
  def gradientOfLogDensity(self, _, arg_list):
    spread = 1.0/(arg_list[1]-arg_list[0])
    return (0, [-spread, spread])
  def logDensityBound(self, x, args): return self.logDensityBoundNumeric(x, *args.operandValues)

  def description(self,name):
    return "  (%s low high) -> samples a uniform real number between low and high." % name

  # TODO Uniform presumably has a variational kernel?

class BetaOutputPSP(RandomPSP):
  # TODO don't need to be class methods
  def simulateNumeric(self,params): return scipy.stats.beta.rvs(*params)
  def logDensityNumeric(self,x,params): return scipy.stats.beta.logpdf(x,*params)

  def simulate(self,args): return self.simulateNumeric(args.operandValues)
  def logDensity(self,x,args): return self.logDensityNumeric(x,args.operandValues)

  def description(self,name):
    return "  (%s alpha beta) returns a sample from a beta distribution with shape parameters alpha and beta." % name

  # TODO Beta presumably has a variational kernel too?

class GammaOutputPSP(RandomPSP):
  # TODO don't need to be class methods
  def simulateNumeric(self,alpha,beta): return scipy.stats.gamma.rvs(alpha,scale=1.0/beta)
  def logDensityNumeric(self,x,alpha,beta): return scipy.stats.gamma.logpdf(x,alpha,scale=1.0/beta)

  def simulate(self,args): return self.simulateNumeric(*args.operandValues)
  def logDensity(self,x,args): return self.logDensityNumeric(x,*args.operandValues)

  def description(self,name):
    return "  (%s alpha beta) returns a sample from a gamma distribution with shape parameter alpha and rate parameter beta." % name

  # TODO Gamma presumably has a variational kernel too?

class StudentTOutputPSP(RandomPSP):
  # TODO don't need to be class methods
  def simulateNumeric(self,nu,loc,scale): return scipy.stats.t.rvs(nu,loc,scale)
  def logDensityNumeric(self,x,nu,loc,scale): return scipy.stats.t.logpdf(x,nu,loc,scale)

  def simulate(self,args):
    loc = args.operandValues[1] if len(args.operandValues) > 1 else 0
    shape = args.operandValues[2] if len(args.operandValues) > 1 else 1
    return self.simulateNumeric(args.operandValues[0],loc,shape)
  def logDensity(self,x,args):
    loc = args.operandValues[1] if len(args.operandValues) > 1 else 0
    shape = args.operandValues[2] if len(args.operandValues) > 1 else 1
    return self.logDensityNumeric(x,args.operandValues[0],loc,shape)

  def description(self,name):
    return "  (%s nu loc shape) returns a sample from Student's t distribution with nu degrees of freedom, with optional location and scale parameters." % name

  # TODO StudentT presumably has a variational kernel too?

class InvGammaOutputPSP(RandomPSP):
  # TODO don't need to be class methods
  def simulateNumeric(self,a,b): return scipy.stats.invgamma.rvs(a,b)
  def logDensityNumeric(self,x,a,b): return scipy.stats.invgamma.logpdf(x,a,b)

  def simulate(self,args): return self.simulateNumeric(*args.operandValues)
  def logDensity(self,x,args): return self.logDensityNumeric(x,*args.operandValues)

  def description(self,name):
    return "(%s nu) -> <number>" % name

  # TODO InvGamma presumably has a variational kernel too?

