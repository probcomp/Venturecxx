# Copyright (c) 2013, 2014, 2015 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

# For some reason, pylint can never find numpy members (presumably metaprogramming).
# pylint: disable=no-member

import math

import numpy as np
import numpy.random as npr
import numpy.linalg as npla
import scipy.stats
import scipy.special
import scipy.special as spsp
import warnings

from exception import VentureValueError, GradientWarning
from lkernel import DeltaLKernel, SimulationAAALKernel
from psp import RandomPSP, DeterministicMakerAAAPSP, NullRequestPSP, RandomPSP,\
  TypedPSP
from sp import SP, SPAux, VentureSPRecord, SPType
from sp_registry import registerBuiltinSP
from sp_help import typed_nr, no_request, dispatching_psp
from utils import logDensityMVNormal, numpy_force_number
from utils import override
import types as t


HALF_LOG2PI = 0.5 * math.log(2 * math.pi)


class NormalDriftKernel(DeltaLKernel):
  def __init__(self, epsilon = 0.7):
    self.epsilon = epsilon

  def forwardSimulate(self, _trace, oldValue, args):
    mu,sigma = args.operandValues()
    nu = scipy.stats.norm.rvs(0,sigma)
    term1 = mu
    term2 = math.sqrt(1 - (self.epsilon * self.epsilon)) * (oldValue - mu)
    term3 = self.epsilon * nu
    return term1 + term2 + term3

  def forwardWeight(self, _trace, _newValue, _oldValue, _args):
    # TODO This is what the code had before the DeltaLKernel refactor;
    # I'm not sure it's right, however.  (Even though this kernel is
    # symmetric, it remains responsible for the prior weight).
    return 0


class MVNormalRandomWalkKernel(DeltaLKernel):
  def __init__(self, epsilon = 0.7):
    self.epsilon = epsilon if epsilon is not None else 0.7

  def simulate(self, _trace, oldValue, args):
    (mu, _) = MVNormalOutputPSP.__parse_args__(args)
    nu = scipy.stats.norm.rvs(0,self.epsilon,mu.shape)
    return oldValue + nu

  @override(DeltaLKernel)
  def forwardWeight(self, _trace, newValue, oldValue, args):
    # log P(_newValue --> _oldValue) == log P(_oldValue --> _newValue)
    (mu, sigma) = MVNormalOutputPSP.__parse_args__(args)
    return logDensityMVNormal(newValue, mu, sigma) - \
      logDensityMVNormal(oldValue, mu, sigma)


class MVNormalOutputPSP(RandomPSP):
  def simulate(self, args):
    return npr.multivariate_normal(*self.__parse_args__(args))

  def logDensity(self, x, args):
    (mu, sigma) = self.__parse_args__(args)
    return logDensityMVNormal(x, mu, sigma)

  def gradientOfLogDensity(self, x, args):
    (mu, sigma) = self.__parse_args__(args)
    isigma = npla.inv(sigma)
    xvar = np.dot(x-mu, x-mu)
    gradX = -np.dot(isigma, np.transpose(x-mu))
    gradMu = np.dot(isigma, np.transpose(x-mu))
    gradSigma = .5*np.dot(np.dot(isigma, xvar),isigma)-.5*isigma
    return np.array(gradX).tolist(), [np.array(gradMu).tolist(), gradSigma]

  def hasDeltaKernel(self):
    return True

  def getDeltaKernel(self, *args):
    return MVNormalRandomWalkKernel(*args)

  def logDensityBound(self, x, args):
    (mu, sigma) = self.__parse_args__(args)
    if sigma is not None:
      # The maximum is obtained when x = mu
      return numpy_force_number(-.5*len(sigma)*np.log(np.pi) - \
        .5*np.log(abs(npla.det(sigma))))
    elif x is not None and mu is not None:
      raise Exception('TODO: Find an analytical form for the maximum of the '\
        'log density of MVNormal for fixed x, mu, but varying sigma')
    else:
      raise Exception("Cannot rejection sample psp with unbounded likelihood")

  def description(self,name):
    return '  %s(mean, covariance) samples a vector according to the '\
      'given multivariate Gaussian distribution.  It is an error if the '\
      'dimensionalities of the arguments do not line up.' % name

  @staticmethod
  def __parse_args__(args):
    (mu, sigma) = args.operandValues()
    return (np.array(mu), np.array(sigma))


registerBuiltinSP("multivariate_normal", typed_nr(MVNormalOutputPSP(),
  [t.HomogeneousArrayType(t.NumberType()), t.SymmetricMatrixType()],
  t.HomogeneousArrayType(t.NumberType())))


class InverseWishartOutputPSP(RandomPSP):
  def simulate(self, args):
    (lmbda, dof) = self.__parse_args__(args)
    p = len(lmbda)

    if dof <= p - 1:
      raise VentureValueError("Degrees of freedom cannot be less than "\
        "dimension of scale matrix")

    try:
      chol = np.linalg.cholesky(lmbda)
    except np.linalg.linalg.LinAlgError, e:
      raise VentureValueError(e)

    # use matlab's heuristic for choosing between the two different sampling schemes
    if (dof <= 81+p) and (dof == int(dof)):
      # direct
      A = np.random.normal(size=(p, dof))
    else:
      # https://en.wikipedia.org/wiki/Wishart_distribution#Bartlett_decomposition
      A = np.diag(np.sqrt(np.random.chisquare(dof - np.arange(p), size=p)))
      A[np.tril_indices_from(A,-1)] = np.random.normal(size=(p*(p-1)//2))
    # inv(A * A.T) = inv(R.T * Q.T * Q * R) = inv(R.T * I * R) = inv(R) * inv(R.T)
    # inv(X * X.T) = chol * inv(A * A.T) * chol.T = chol * inv(R) * inv(R.T) * chol.T
    # TODO why do the QR decomposition here? it seems slower than solving directly
    R = np.linalg.qr(A.T, 'r')
    # NB: have to pass lower=True because R.T is a lower-triangular matrix
    T = scipy.linalg.solve_triangular(R.T, chol.T, lower=True)
    return np.dot(T.T, T)

  def logDensity(self, x, args):
    (lmbda, dof) = self.__parse_args__(args)
    p = len(lmbda)
    log_density =  dof/2*(np.log(npla.det(lmbda)) - p*np.log(2)) \
      - spsp.multigammaln(dof*.5, p) \
      + (-.5*(dof+p+1))*np.log(npla.det(x)) \
      - .5*np.trace(np.dot(lmbda, npla.inv(x)))
    return log_density

  def gradientOfLogDensity(self, X, args):
    '''
    Based on the following Wikipedia page:
      http://en.wikipedia.org/wiki/Inverse-Wishart_distribution
      http://en.wikipedia.org/wiki/Multivariate_gamma_function
      http://en.wikipedia.org/wiki/Matrix_calculus
    '''
    (lmbda, dof) = self.__parse_args__(args)
    p = len(lmbda)
    invX = npla.inv(X)
    invLmbda = npla.inv(lmbda)
    gradX = -.5*(dof+p+1)*invX + .5*np.dot(invX, np.dot(lmbda, invX))
    gradLmbda = .5*dof*invLmbda - .5*invX
    gradDof = .5*np.log(npla.det(lmbda))-.5*np.log(npla.det(X))-.5*p*np.log(2)
    for i in range(p):
      gradDof = gradDof-.5*spsp.psi(.5*(dof-i))
    return gradX, [gradLmbda, gradDof]

  def description(self,name):
    return "  %s(scale_matrix, degree_of_freedeom) samples a positive "\
      "definite matrix according to the given inverse Wishart distribution."\
      % name

  def __parse_args__(self, args):
    (lmbda, dof) = args.operandValues()
    return (np.array(lmbda), dof)


registerBuiltinSP("inv_wishart", typed_nr(InverseWishartOutputPSP(),
  [t.SymmetricMatrixType(), t.PositiveType()], t.SymmetricMatrixType()))


class WishartOutputPSP(RandomPSP):
  '''
  Returns a sample from the Wishart distribution, conjugate prior for
  precision matrices.
  '''
  def simulate(self, args):
    (sigma, dof) = self.__parse_args__(args)
    p = len(sigma)

    if dof <= p - 1:
      raise VentureValueError("Degrees of freedom cannot be less than "\
        "dimension of scale matrix")

    try:
      chol = np.linalg.cholesky(sigma)
    except np.linalg.linalg.LinAlgError, e:
      raise VentureValueError(e)

    # Use Matlab's heuristic for choosing between the two different sampling schemes.
    if (dof <= 81+p) and (dof == int(dof)):
      # direct
      A = np.random.normal(size=(p, dof))
    else:
      # https://en.wikipedia.org/wiki/Wishart_distribution#Bartlett_decomposition
      A = np.diag(np.sqrt(np.random.chisquare(dof - np.arange(p), size=p)))
      A[np.tril_indices_from(A,-1)] = np.random.normal(size=(p*(p-1)//2))
    X = np.dot(chol, A)
    return np.dot(X, X.T)

  def logDensity(self, X, args):
    (sigma, dof) = self.__parse_args__(args)
    invSigma = npla.inv(sigma)
    p = len(sigma)
    log_density =  -.5*dof*(np.log(npla.det(sigma)) + p*np.log(2)) \
      - spsp.multigammaln(dof*.5, p) \
      + .5*(dof-p-1)*np.log(npla.det(X)) - .5*np.trace(np.dot(invSigma, X))
    return log_density

  def gradientOfLogDensity(self, X, args):
    '''
    Based on the following Wikipedia page:
      http://en.wikipedia.org/wiki/Inverse-Wishart_distribution
      http://en.wikipedia.org/wiki/Multivariate_gamma_function
      http://en.wikipedia.org/wiki/Matrix_calculus
    '''
    (sigma, dof) = self.__parse_args__(args)
    p = len(sigma)
    invX = npla.inv(X)
    invSigma = npla.inv(sigma)
    gradX = .5*(dof-p-1)*invX-.5*invSigma
    gradSigma = -.5*invSigma+.5*np.dot(invSigma, np.dot(X, invSigma))
    gradDof = .5*np.log(npla.det(X))-.5*p*np.log(2)-.5*np.log(npla.det(sigma))
    for i in range(p):
      gradDof = gradDof-.5*spsp.psi(.5*(dof-i))
    return gradX, [gradSigma, gradDof]

  def description(self,name):
    return "  %s(scale_matrix, degree_of_freedeom) samples a positive "\
      "definite matrix according to the given inverse Wishart distribution."\
      % name

  def __parse_args__(self, args):
    (sigma, dof) = args.operandValues()
    return (np.array(sigma), dof)


registerBuiltinSP("wishart", typed_nr(WishartOutputPSP(),
  [t.SymmetricMatrixType(), t.PositiveType()], t.SymmetricMatrixType()))


class NormalOutputPSP(RandomPSP):
  # TODO don't need to be class methods
  def simulateNumeric(self,params):
    return scipy.stats.norm.rvs(*params)

  def logDensityNumeric(self,x,params):
    (mu, sigma) = params
    deviation = x - mu
    return - math.log(sigma) - HALF_LOG2PI \
      - (0.5 * deviation * deviation / (sigma * sigma))

  def logDensityBoundNumeric(self, x, mu, sigma):
    if sigma is not None:
      return -(math.log(sigma) + HALF_LOG2PI)
    elif x is not None and mu is not None:
      # Per the derivative of the log density noted in the
      # gradientOfLogDensity method, the maximum occurs when
      # (x-mu)^2 = sigma^2
      return self.logDensityNumeric(x, [mu, abs(x-mu)])
    else:
      raise Exception("Cannot rejection sample psp with unbounded likelihood")

  def simulate(self, args):
    return self.simulateNumeric(args.operandValues())

  def gradientOfSimulate(self, args, value, direction):
    # Reverse engineering the behavior of scipy.stats.norm.rvs
    # suggests this gradient is correct.
    (mu, sigma) = args.operandValues()
    deviation = (value - mu) / sigma
    return [direction*1, direction*deviation]

  def logDensity(self, x, args):
    return self.logDensityNumeric(x,args.operandValues())

  def logDensityBound(self, x, args):
    return self.logDensityBoundNumeric(x, *args.operandValues())

  def hasDeltaKernel(self):
    return False # have each gkernel control whether it is delta or not

  def getDeltaKernel(self, args):
    return NormalDriftKernel(args)

  def hasVariationalLKernel(self):
    return True

  def getParameterScopes(self):
    return ["REAL","POSITIVE_REAL"]

  def gradientOfLogDensity(self,x,args):
    (mu, sigma) = args.operandValues()
    gradX = -(x - mu) / (math.pow(sigma,2))
    gradMu = (x - mu) / (math.pow(sigma,2))
    gradSigma = (math.pow(x - mu,2) - math.pow(sigma,2)) / math.pow(sigma,3)
    # for positive sigma, d(log density)/d(sigma) is <=> zero
    # when math.pow(x - mu,2) <=> math.pow(sigma,2) respectively
    return (gradX,[gradMu,gradSigma])

  def description(self,name):
    return "  %s(mu, sigma) samples a normal distribution with mean mu "\
      "and standard deviation sigma." % name


class NormalvvOutputPSP(RandomPSP):
  def simulate(self, args):
    return np.random.normal(*args.operandValues())

  def logDensity(self, x, args):
    return sum(scipy.stats.norm.logpdf(x, *args.operandValues()))

  def gradientOfLogDensity(self,x,args):
    (mu, sigma) = args.operandValues()
    gradX = -(x - mu) / (np.power(sigma,2))
    gradMu = (x - mu) / (np.power(sigma,2))
    gradSigma = (np.power(x - mu,2) - np.power(sigma,2)) / np.power(sigma,3)
    return (gradX,[gradMu,gradSigma])


# These two only differ because the gradients need to account for broadcasting
class NormalsvOutputPSP(RandomPSP):
  def simulate(self, args):
    return np.random.normal(*args.operandValues())

  def logDensity(self, x, args):
    return sum(scipy.stats.norm.logpdf(x, *args.operandValues()))

  def gradientOfLogDensity(self, x, args):
    (mu, sigma) = args.operandValues()
    gradX = -(x - mu) / (np.power(sigma,2))
    gradMu = (x - mu) / (np.power(sigma,2))
    gradSigma = (np.power(x - mu,2) - np.power(sigma,2)) / np.power(sigma,3)
    return (gradX,[sum(gradMu),gradSigma])


class NormalvsOutputPSP(RandomPSP):
  def simulate(self, args):
    return np.random.normal(*args.operandValues())

  def logDensity(self, x, args):
    return sum(scipy.stats.norm.logpdf(x, *args.operandValues()))

  def gradientOfLogDensity(self, x, args):
    (mu, sigma) = args.operandValues()
    gradX = -(x - mu) / (np.power(sigma,2))
    gradMu = (x - mu) / (np.power(sigma,2))
    gradSigma = (np.power(x - mu,2) - np.power(sigma,2)) / np.power(sigma,3)
    return (gradX,[gradMu,sum(gradSigma)])


generic_normal = dispatching_psp(
  [SPType([t.NumberType(), t.NumberType()], t.NumberType()), # TODO Sigma is really non-zero, but negative is OK by scaling
    SPType([t.NumberType(), t.ArrayUnboxedType(t.NumberType())],
      t.ArrayUnboxedType(t.NumberType())),
    SPType([t.ArrayUnboxedType(t.NumberType()), t.NumberType()],
      t.ArrayUnboxedType(t.NumberType())),
    SPType([t.ArrayUnboxedType(t.NumberType()),
      t.ArrayUnboxedType(t.NumberType())], t.ArrayUnboxedType(t.NumberType()))],
  [NormalOutputPSP(), NormalsvOutputPSP(), NormalvsOutputPSP(),
    NormalvvOutputPSP()])

registerBuiltinSP("normal", no_request(generic_normal))


class VonMisesOutputPSP(RandomPSP):
  def simulate(self, args):
    (mu, kappa) = args.operandValues()
    return scipy.stats.vonmises.rvs(kappa, loc=mu)

  def logDensity(self, x, args):
    (mu, kappa) = args.operandValues()
    # k * cos (x - mu) - log(2pi I_0(k))
    return scipy.stats.vonmises.logpdf(x, kappa, loc=mu)

  def logDensityBound(self, x, args):
    (mu, kappa) = args.operandValues()
    if kappa is not None:
      return scipy.stats.vonmises.logpdf(0, kappa)
    elif x is not None and mu is not None:
      raise Exception("TODO What is the bound for a vonmises varying kappa?")
    else:
      raise Exception("Cannot rejection sample psp with unbounded likelihood")

  def gradientOfLogDensity(self, x, args):
    (mu, kappa) = args.operandValues()
    gradX  = -math.sin(x - mu) * kappa
    gradMu = math.sin(x - mu) * kappa
    # d/dk(log density) = cos(x-mu) - [2pi d(I_0)(k)]/2pi I_0(k)
    # d/dk I_0(k) = I_1(k)
    gradK  = math.cos(x - mu) - (scipy.special.i1(kappa) \
      / scipy.special.i0(kappa))
    return (gradX, [gradMu, gradK])

  def description(self,name):
    return "  %s(mu, kappa) samples a von Mises distribution with mean mu and "\
      "shape kappa. The output is normalized to the interval [-pi,pi]." % name


registerBuiltinSP("vonmises", typed_nr(VonMisesOutputPSP(),
  [t.NumberType(), t.PositiveType()], t.NumberType()))


class UniformOutputPSP(RandomPSP):
  # TODO don't need to be class methods
  def simulateNumeric(self, low, high):
    return scipy.stats.uniform.rvs(low, high-low)

  def logDensityNumeric(self, x, low, high):
    return scipy.stats.uniform.logpdf(x, low, high-low)

  def logDensityBoundNumeric(self, _, low, high):
    if low is None or high is None:
      # Unbounded
      raise Exception("Cannot rejection sample psp with unbounded likelihood")
    else:
      return -math.log(high - low)

  def simulate(self, args):
    return self.simulateNumeric(*args.operandValues())

  def logDensity(self, x, args):
    return self.logDensityNumeric(x,*args.operandValues())

  def gradientOfLogDensity(self, _, args):
    (low, high) = args.operandValues()
    spread = 1.0 / (high - low)
    return (0, [spread, -spread])

  def logDensityBound(self, x, args):
    return self.logDensityBoundNumeric(x, *args.operandValues())

  def description(self, name):
    return "  %s(low, high) samples a uniform real number between low "\
      "and high." % name

  # TODO Uniform presumably has a variational kernel?


registerBuiltinSP("uniform_continuous",typed_nr(UniformOutputPSP(),
  [t.NumberType(), t.NumberType()], t.NumberType()))


class BetaOutputPSP(RandomPSP):
  # TODO don't need to be class methods
  def simulateNumeric(self, params):
    return scipy.stats.beta.rvs(*params)

  def logDensityNumeric(self, x, params):
    return scipy.stats.beta.logpdf(x,*params)

  def simulate(self, args):
    return self.simulateNumeric(args.operandValues())

  def logDensity(self, x, args):
    return self.logDensityNumeric(x,args.operandValues())

  def gradientOfLogDensity(self, x, args):
    (alpha, beta) = args.operandValues()
    gradX = ((float(alpha) - 1) / x) - ((float(beta) - 1) / (1 - x))
    gradAlpha = spsp.digamma(alpha + beta) - spsp.digamma(alpha) + math.log(x)
    gradBeta = spsp.digamma(alpha + beta) - spsp.digamma(beta) + math.log(1 - x)
    return (gradX,[gradAlpha,gradBeta])

  def description(self, name):
    return "  %s(alpha, beta) returns a sample from a Beta distribution with "\
      "shape parameters alpha and beta." % name

  # TODO Beta presumably has a variational kernel too?


registerBuiltinSP("beta", typed_nr(BetaOutputPSP(),
  [t.PositiveType(), t.PositiveType()], t.ProbabilityType()))


class ExponOutputPSP(RandomPSP):
  # TODO don't need to be class methods
  def simulateNumeric(self, theta):
    return scipy.stats.expon.rvs(scale=1.0/theta)

  def logDensityNumeric(self, x, theta):
    return scipy.stats.expon.logpdf(x,scale=1.0/theta)

  def simulate(self,args):
    return self.simulateNumeric(*args.operandValues())

  def logDensity(self,x,args):
    return self.logDensityNumeric(x,*args.operandValues())

  def gradientOfLogDensity(self,x,args):
    theta = args.operandValues()[0]
    gradX = -theta
    gradTheta = 1. / theta - x
    return (gradX,[gradTheta])

  def description(self,name):
    return "  %s(theta) returns a sample from an exponential distribution "\
      "with rate (inverse scale) parameter theta." % name


registerBuiltinSP("expon", typed_nr(ExponOutputPSP(),
  [t.PositiveType()], t.PositiveType()))


class GammaOutputPSP(RandomPSP):
  # TODO don't need to be class methods
  def simulateNumeric(self, alpha, beta):
    return scipy.stats.gamma.rvs(alpha, scale=1.0/beta)

  def logDensityNumeric(self, x, alpha, beta):
    return scipy.stats.gamma.logpdf(x, alpha, scale=1.0/beta)

  def simulate(self, args):
    return self.simulateNumeric(*args.operandValues())

  def gradientOfSimulate(self, args, value, direction):
    # These gradients were computed by Sympy; the script to get them is
    # in doc/gradients.py
    alpha, beta = args.operandValues()
    if alpha == 1:
      warnstr = ('Gradient of simulate is discontinuous at alpha = 1.\n'
                 'Issue https://app.asana.com/0/11192551635048/14271708124534.')
      warnings.warn(warnstr, GradientWarning)
      gradAlpha = 0
      gradBeta = -value / math.pow(beta, 2.0)
    elif alpha > 1:
      x0 = value / (3.0 * alpha - 1)
      gradAlpha = (-3.0 * x0 / 2 + 3 * 3 ** (2.0 / 3) *
                   (beta * x0) ** (2.0 / 3) / (2.0 * beta))
      gradBeta = -value/beta
    else:
      if value <= (1.0 / beta) * math.pow(1 - alpha, 1.0 / alpha):
        x0 = (beta * value) ** alpha
        gradAlpha = -x0 ** (1.0 / alpha) * math.log(x0) / (alpha ** 2.0 * beta)
        gradBeta = -((beta * value) ** alpha) ** (1.0 / alpha) / beta ** 2.0
      else:
        x0 = -alpha + 1
        x1 = 1.0 / alpha
        x2 = alpha * math.log(math.exp(x1 * (x0 - (beta * value) ** alpha)))
        x3 = -x2
        x4 = x0 + x3
        gradAlpha = (x4 ** (x0 * x1) * (x3 + (alpha + x2 - 1) *
                     math.log(x4)) / (alpha ** 2.0 * beta))
        x0 = 1.0 / alpha
        gradBeta = ( -(-alpha * math.log(math.exp(-x0 * (alpha +
          (beta * value) ** alpha - 1))) - alpha + 1) ** x0 / beta ** 2.0 )
    return [direction * gradAlpha, direction * gradBeta]

  def logDensity(self, x, args):
    return self.logDensityNumeric(x,*args.operandValues())

  def gradientOfLogDensity(self, x, args):
    (alpha, beta) = args.operandValues()
    gradX = ((alpha - 1) / float(x)) - beta
    gradAlpha = math.log(beta) - spsp.digamma(alpha) + math.log(x)
    gradBeta = (float(alpha) / beta) - x
    return (gradX,[gradAlpha,gradBeta])

  def description(self, name):
    return "  %s(alpha, beta) returns a sample from a Gamma distribution "\
      "with shape parameter alpha and rate parameter beta." % name

  # TODO Gamma presumably has a variational kernel too?


registerBuiltinSP("gamma", typed_nr(GammaOutputPSP(),
  [t.PositiveType(), t.PositiveType()], t.PositiveType()))


class StudentTOutputPSP(RandomPSP):
  # TODO don't need to be class methods
  def simulateNumeric(self, nu, loc, scale):
    return scipy.stats.t.rvs(nu,loc,scale)

  def logDensityNumeric(self, x, nu, loc, scale):
    return scipy.stats.t.logpdf(x,nu,loc,scale)

  def simulate(self, args):
    vals = args.operandValues()
    loc = vals[1] if len(vals) > 1 else 0
    shape = vals[2] if len(vals) > 1 else 1
    return self.simulateNumeric(vals[0],loc,shape)

  def logDensity(self, x, args):
    vals = args.operandValues()
    loc = vals[1] if len(vals) > 1 else 0
    shape = vals[2] if len(vals) > 1 else 1
    return self.logDensityNumeric(x,vals[0],loc,shape)

  def gradientOfLogDensity(self, x, args):
    vals = args.operandValues()
    nu = vals[0]
    loc = vals[1] if len(vals) > 1 else 0
    shape = vals[2] if len(vals) > 1 else 1
    gradX = (loc - x) * (nu + 1) / (nu * shape ** 2 + (loc - x) ** 2)
    # we'll do gradNu in pieces because it's messy
    x0 = 1.0 / nu
    x1 = shape ** 2
    x2 = nu * x1
    x3 = (loc - x) ** 2
    x4 = x2 + x3
    x5 = nu / 2.0
    gradNu = (x0 * (nu * x4 * (-math.log(x0 * x4 / x1) - spsp.digamma(x5)
              + spsp.digamma(x5 + 1.0 / 2)) - x2
              + x3 * (nu + 1) - x3) / (2.0 * x4))
    if len(vals) == 1:
      return (gradX,[gradNu])
    gradLoc = -(loc - x) * (nu + 1) / (nu * shape ** 2 + (loc - x) ** 2)
    gradShape = ((-nu * shape ** 2 + (loc - x) ** 2 * (nu + 1) -
                 (loc - x) ** 2) / (shape * (nu * shape ** 2 + (loc - x) ** 2)))
    return (gradX,[gradNu,gradLoc,gradShape])

  def description(self, name):
    return "  %s(nu, loc, shape) returns a sample from Student's t "\
      "distribution with nu degrees of freedom, with optional location "\
      "and scale parameters." % name

  # TODO StudentT presumably has a variational kernel too?


registerBuiltinSP("student_t", typed_nr(StudentTOutputPSP(),
  [t.PositiveType(), t.NumberType(), t.NumberType()], t.NumberType(),
  min_req_args=1 ))


class InvGammaOutputPSP(RandomPSP):
  # TODO don't need to be class methods
  def simulateNumeric(self, a, b):
    return scipy.stats.invgamma.rvs(a, scale=b)

  def logDensityNumeric(self, x, a, b):
    return scipy.stats.invgamma.logpdf(x, a, scale=b)

  def simulate(self, args):
    return self.simulateNumeric(*args.operandValues())

  def logDensity(self, x, args):
    return self.logDensityNumeric(x, *args.operandValues())

  def gradientOfLogDensity(self, x, args):
    (alpha, beta) = args.operandValues()
    gradX = (1.0 / x) * (-alpha - 1 + (beta / x))
    gradAlpha = math.log(beta) - spsp.digamma(alpha) - math.log(x)
    gradBeta = (float(alpha) / beta) - (1.0 / x)
    return (gradX,[gradAlpha,gradBeta])

  def description(self,name):
    return "%s(alpha, beta) returns a sample from an inverse Gamma "\
      "distribution with shape parameter alpha and scale parameter beta" % name

  # TODO InvGamma presumably has a variational kernel too?


registerBuiltinSP("inv_gamma", typed_nr(InvGammaOutputPSP(),
  [t.PositiveType(), t.PositiveType()], t.PositiveType()))


class LaplaceOutputPSP(RandomPSP):
  # a is the location, b is the scale; parametrization is same as Wikipedia
  def simulateNumeric(self, a, b):
    return scipy.stats.laplace.rvs(a,b)

  def logDensityNumeric(self, x, a, b):
    return scipy.stats.laplace.logpdf(x,a,b)

  def simulate(self, args):
    return self.simulateNumeric(*args.operandValues())

  def logDensity(self, x, args):
    return self.logDensityNumeric(x,*args.operandValues())

  def gradientOfLogDensity(self,x,args):
    (a, b) = args.operandValues()
    # if we're at the cusp point, play it safe and go undefined
    if x == a:
      gradX = np.nan
      gradA = np.nan
    else:
      xgta = float(np.sign(x - a))
      gradX = -xgta / b
      gradA = xgta / b
    gradB = (-1. / b) + abs(x - float(a)) / (b ** 2)
    return (gradX,[gradA,gradB])

  def description(self,name):
    return "%s(a, b) returns a sample from a Laplace (double exponential) "\
      "distribution with shape parameter a and scale parameter b" % name


registerBuiltinSP("laplace", typed_nr(LaplaceOutputPSP(),
  [t.NumberType(), t.PositiveType()], t.NumberType()))


# SP for Normal, maintaining sufficient statistics.
class SuffNormalSP(SP):
  def constructSPAux(self):
    return SuffNormalSPAux()

  def show(self,spaux):
    return spaux.cts()


# SPAux for Normal. The sufficent statistics for N observations are N (ctN),
# sum (xsum) and sum squares (xsumsq)
class SuffNormalSPAux(SPAux):
  def __init__(self):
    self.ctN = 0
    self.xsum = 0.0
    self.xsumsq = 0.0

  def copy(self):
    aux = SuffNormalSPAux()
    aux.ctN = self.ctN
    aux.xsum = self.xsum
    aux.xsumsq = self.xsumsq
    return aux

  v_type = t.HomogeneousListType(t.NumberType())

  def asVentureValue(self):
    return SuffNormalSPAux.v_type.asVentureValue([self.ctN, self.xsum,
        self.xsumsq])

  @staticmethod
  def fromVentureValue(val):
    aux = SuffNormalSPAux()
    (aux.ctN, aux.xsum, aux.xsumsq) = SuffNormalSPAux.v_type.asPython(val)
    return aux

  def cts(self):
    return [self.ctN, self.xsum, self.xsumsq]


# Generic Normal PSP maintaining sufficient statistics.
class SuffNormalOutputPSP(RandomPSP):
  def __init__(self, mu, sigma):
    self.mu = mu
    self.sigma = sigma

  def incorporate(self, value, args):
    spaux = args.spaux()
    spaux.ctN += 1
    spaux.xsum += value
    spaux.xsumsq += value * value

  def unincorporate(self, value, args):
    spaux = args.spaux()
    spaux.ctN -= 1
    spaux.xsum -= value
    spaux.xsumsq -= value * value

  def simulate(self, _args):
    return scipy.stats.norm.rvs(loc=self.mu, scale=self.sigma)

  def logDensity(self, value, _args):
    return scipy.stats.norm.logpdf(value, loc=self.mu, scale=self.sigma)

  def logDensityOfCounts(self, aux):
    return SuffNormalOutputPSP.logDensityOfCountsNumeric(aux, self.mu, self.sigma)

  @staticmethod
  def logDensityOfCountsNumeric(aux, mu, sigma):
    # Derived from:
    # http://www.encyclopediaofmath.org/index.php/Sufficient_statistic
    # See doc/sp-math/
    [ctN, xsum, xsumsq] = aux.cts()
    term1 = -ctN/2. * ( math.log(2*math.pi) + 2*math.log(sigma) )
    term2 = -ctN/2. * mu**2 / sigma**2
    term3 = -1/(2*sigma**2) * xsumsq
    term4 = mu/sigma**2 * xsum
    return term1 + term2 + term3 + term4


class UNigNormalOutputPSP(SuffNormalOutputPSP):
# Collapsed NormalInverseGamma (prior) for Normal (likelihood)
  pass


# Collapsed NormalInverseGamma (prior) for Normal (likelihood)
# http://www.cs.ubc.ca/~murphyk/Papers/bayesGauss.pdf#page=16
class CNigNormalOutputPSP(RandomPSP):
  def __init__(self, m, V, a, b):
    assert isinstance(m, float)
    assert isinstance(V, float)
    assert isinstance(a, float)
    assert isinstance(b, float)
    self.m = m
    self.V = V
    self.a = a
    self.b = b

  def incorporate(self, value, args):
    spaux = args.spaux()
    spaux.ctN += 1
    spaux.xsum += value
    spaux.xsumsq += value * value

  def unincorporate(self, value, args):
    spaux = args.spaux()
    spaux.ctN -= 1
    spaux.xsum -= value
    spaux.xsumsq -= value * value

  def updatedParams(self, aux):
    return CNigNormalOutputPSP.posteriorHypersNumeric \
      ((self.m, self.V, self.a, self.b), aux.cts())

  def simulate(self, args):
    # Posterior predictive is Student's t (206)
    (mn, Vn, an, bn) = self.updatedParams(args.spaux())
    return scipy.stats.t.rvs(2*an, loc=mn, scale=math.sqrt(bn/an*(1+Vn)))

  def logDensity(self, value, args):
    (mn, Vn, an, bn) = self.updatedParams(args.spaux())
    return scipy.stats.t.logpdf(value, 2*an, loc=mn,
      scale=math.sqrt(bn/an*(1+Vn)))

  def logDensityOfCounts(self, aux):
    # Marginal likelihood of the data (203)
    [ctN, xsum, xsumsq] = aux.cts()
    (mn, Vn, an, bn) = self.updatedParams(aux)
    term1 = 0.5 * math.log(abs(Vn)) - 0.5 * math.log(abs(self.V))
    term2 = self.a * math.log(self.b) - an * math.log(bn)
    term3 = scipy.special.gammaln(an) - scipy.special.gammaln(self.a)
    term4 = math.log(1) - ctN/2. * math.log(math.pi) - ctN * math.log(2)
    return term1 + term2 + term3 + term4

  @staticmethod
  def posteriorHypersNumeric(prior_hypers, counts):
    # http://www.cs.ubc.ca/~murphyk/Papers/bayesGauss.pdf#page=16
    # (197 - 200)
    [m, V, a, b] = prior_hypers
    [ctN, xsum, xsumsq] = counts
    Vn = 1 / (1/V + ctN)
    mn = Vn*(1/V*m + xsum)
    an = a + ctN / 2
    bn = b + 0.5*(m**2/V + xsumsq - mn**2/Vn)
    return (mn, Vn, an, bn)

# Maker for Collapsed NIG-Normal
class MakerCNigNormalOutputPSP(DeterministicMakerAAAPSP):
  def simulate(self, args):
    (m, V, a, b) = args.operandValues()
    output = TypedPSP(CNigNormalOutputPSP(m, V, a, b), SPType([],
        t.NumberType()))
    return VentureSPRecord(SuffNormalSP(NullRequestPSP(), output))

  def description(self, name):
    return '  %s(m,V,a,b) returns collapsed NormalInverseGamma Normal '\
        'sampler. While this procedure itself is deterministic, the returned '\
        'sampler is stochastic.' % name

registerBuiltinSP("make_nig_normal", typed_nr(MakerCNigNormalOutputPSP(),
  [t.NumberType(), t.PositiveType(), t.PositiveType(),t.PositiveType()],
  SPType([], t.NumberType())))


# Uncollapsed AAA NigNormal
class MakerUNigNormalOutputPSP(RandomPSP):
  def childrenCanAAA(self):
    return True

  def getAAALKernel(self):
    return UNigNormalAAALKernel()

  def simulate(self, args):
    (m, V, a, b) = args.operandValues()
    # Simulate the mean and variance from NormalInverseGamma.
    # https://en.wikipedia.org/wiki/Normal-inverse-gamma_distribution#Generating_normal-inverse-gamma_random_variates
    sigma2 = scipy.stats.invgamma.rvs(a, scale=b)
    mu = scipy.stats.norm.rvs(loc=m, scale=math.sqrt(sigma2*V))
    output = TypedPSP(UNigNormalOutputPSP(mu, math.sqrt(sigma2)),
      SPType([], t.NumberType()))
    return VentureSPRecord(SuffNormalSP(NullRequestPSP(), output))

  def logDensity(self, value, args):
    assert isinstance(value, VentureSPRecord)
    assert isinstance(value.sp, SuffNormalSP)
    (m, V, a, b) = args.operandValues()
    mu = value.sp.outputPSP.psp.mu
    sigma2 = value.sp.outputPSP.psp.sigma**2
    return scipy.stats.invgamma.logpdf(sigma2, a, scale=b) + \
      scipy.stats.norm.logpdf(mu, loc=m, scale=math.sqrt(sigma2*V))

  def description(self, name):
    return '  %s(alpha, beta) returns an uncollapsed Normal-InverseGamma '\
      'Normal sampler.' % name


class UNigNormalAAALKernel(SimulationAAALKernel):
  def simulate(self, _trace, args):
    madeaux = args.madeSPAux()
    (mn, Vn, an, bn) = CNigNormalOutputPSP.posteriorHypersNumeric \
      (args.operandValues(), madeaux.cts())
    newSigma2 = scipy.stats.invgamma.rvs(an, scale=bn)
    newMu = scipy.stats.norm.rvs(loc=mn, scale = math.sqrt(newSigma2*Vn))
    output = TypedPSP(SuffNormalOutputPSP(newMu, math.sqrt(newSigma2)),
      SPType([], t.NumberType()))
    return VentureSPRecord(SuffNormalSP(NullRequestPSP(), output), madeaux)

  def weight(self, _trace, _newValue, _args):
    # Gibbs step, samples exactly from the local posterior.  Being a
    # AAALKernel, this one gets to cancel against the likelihood as
    # well as the prior.
    return 0

  def weightBound(self, _trace, _value, _args):
    return 0


registerBuiltinSP("make_uc_nig_normal", typed_nr(MakerUNigNormalOutputPSP(),
  [t.NumberType(), t.PositiveType(), t.PositiveType(), t.PositiveType()],
  SPType([], t.NumberType())))


# Non-conjugate AAA Normal
class MakerSuffNormalOutputPSP(DeterministicMakerAAAPSP):
  def simulate(self, args):
    (mu, sigma) = args.operandValues()
    output = TypedPSP(SuffNormalOutputPSP(mu, sigma), SPType([],
      t.NumberType()))
    return VentureSPRecord(SuffNormalSP(NullRequestPSP(), output))

  def description(self,name):
    return '  %s(mu, sigma) returns Normal sampler with given mean and sigma. '\
      'While this procedure itself is deterministic, the returned sampler '\
      'is stochastic. The latter maintains application statistics sufficient '\
      'to absorb changes to the weight in O(1) time (without traversing all '\
      'the applications.' % name

  def gradientOfLogDensityOfCounts(self, aux, args):
    """The derivatives with respect to the args of the log density of the counts
    collected by the made SP."""
    # See the derivation in doc/sp-math/
    (mu, sigma) = args.operandValues()
    [ctN, xsum, xsumsq] = aux.cts()
    xsumsq_dev = xsumsq - 2*mu*xsum + ctN*mu**2
    grad_mu =  (xsum - ctN*mu) / sigma**2
    grad_sigma = -ctN / sigma + xsumsq_dev / sigma**3
    return [grad_mu, grad_sigma]

  def madeSpLogDensityOfCountsBound(self, aux):
    [ctN, xsum, xsumsq] = aux.cts()
    if ctN == 0:
      return 0
    mu_hat = xsum / ctN
    sigma_hat = math.sqrt(xsumsq / ctN - xsum ** 2 / ctN ** 2)
    return SuffNormalOutputPSP.logDensityOfCountsNumeric(aux, mu_hat, sigma_hat)

registerBuiltinSP("make_suff_stat_normal", typed_nr(MakerSuffNormalOutputPSP(),
  [t.NumberType(), t.PositiveType()], SPType([], t.NumberType())))
