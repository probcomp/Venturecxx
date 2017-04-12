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

from __future__ import division

import math
import warnings

import numpy as np
import numpy.linalg as npla
import scipy.special as spsp
import scipy.stats

from scipy.special import betaln
from scipy.special import digamma

from venture.lite.exception import GradientWarning
from venture.lite.exception import VentureValueError
from venture.lite.lkernel import DeltaLKernel
from venture.lite.lkernel import PosteriorAAALKernel
from venture.lite.psp import DeterministicMakerAAAPSP
from venture.lite.psp import NullRequestPSP
from venture.lite.psp import RandomPSP
from venture.lite.psp import TypedPSP
from venture.lite.sp import SP
from venture.lite.sp import SPAux
from venture.lite.sp import SPType
from venture.lite.sp import VentureSPRecord
from venture.lite.sp_help import dispatching_psp
from venture.lite.sp_help import no_request
from venture.lite.sp_help import typed_nr
from venture.lite.sp_registry import registerBuiltinSP
from venture.lite.utils import exp
from venture.lite.utils import expm1
from venture.lite.utils import log
from venture.lite.utils import log1p
from venture.lite.utils import logDensityMVNormal
from venture.lite.utils import log_d_logistic
from venture.lite.utils import log_logistic
from venture.lite.utils import logistic
from venture.lite.utils import logit
from venture.lite.utils import logsumexp
from venture.lite.utils import override
from venture.lite.utils import simulateLogGamma
import venture.lite.types as t


HALF_LOG2PI = 0.5 * math.log(2 * math.pi)


class NormalDriftKernel(DeltaLKernel):
  def __init__(self, epsilon = 0.7):
    self.epsilon = epsilon

  def forwardSimulate(self, _trace, oldValue, args):
    mu,sigma = args.operandValues()
    nu = args.np_prng().normal(loc=0, scale=sigma)
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
    nu = args.np_prng().normal(loc=0, scale=self.epsilon, size=mu.shape)
    return oldValue + nu

  @override(DeltaLKernel)
  def forwardWeight(self, _trace, newValue, oldValue, args):
    # log P(_newValue --> _oldValue) == log P(_oldValue --> _newValue)
    (mu, sigma) = MVNormalOutputPSP.__parse_args__(args)
    return logDensityMVNormal(newValue, mu, sigma) - \
      logDensityMVNormal(oldValue, mu, sigma)


class MVNormalOutputPSP(RandomPSP):
  def simulate(self, args):
    return args.np_prng().multivariate_normal(*self.__parse_args__(args))

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
      return float(-.5*len(sigma)*np.log(np.pi) -
        .5*np.log(abs(npla.det(sigma))))
    elif x is not None and mu is not None:
      raise Exception('TODO: Find an analytical form for the maximum of the '\
        'log density of MVNormal for fixed x, mu, but varying sigma')
    else:
      raise Exception("Cannot rejection auto-bound psp with unbounded likelihood")

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
  # Parameterization follows Wikipedia
  # https://en.wikipedia.org/wiki/Inverse-Wishart_distribution, namely
  # - lmbda is a p by p positive definite scale matrix
  # - dof > p - 1 is the degrees of freedom
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
      A = args.np_prng().normal(size=(p, int(dof)))
    else:
      # https://en.wikipedia.org/wiki/Wishart_distribution#Bartlett_decomposition
      A = np.diag(np.sqrt(args.np_prng().chisquare(dof - np.arange(p), size=p)))
      A[np.tril_indices_from(A,-1)] = args.np_prng().normal(size=(p*(p-1)//2))
    # inv(A * A.T) = inv(R.T * Q.T * Q * R) = inv(R.T * I * R) = inv(R) * inv(R.T)
    # inv(X * X.T) = chol * inv(A * A.T) * chol.T = chol * inv(R) * inv(R.T) * chol.T
    # TODO why do the QR decomposition here? it seems slower than solving directly
    R = np.linalg.qr(A.T, 'r')
    # NB: have to pass lower=True because R.T is a lower-triangular matrix
    T = scipy.linalg.solve_triangular(R.T, chol.T, lower=True)
    return np.dot(T.T, T)

  # PDF formula from Wikipedia cross-checked against Murphy [1, Sec
  # 4.5.1, p.127].  They agree with the following translation
  # dictionary:
  # Murphy | Wiki
  # S^-1   | Psi
  # Sigma  | X
  # D      | p
  # nu     | nu
  # and the published erratum to eq. 4.166 in [1] "In the
  # normalization of inverse Wishart, the exponent of |S| shouldn't be
  # negated."  See derivation of logarithm in sp-math.tex.
  def logDensity(self, x, args):
    def logdet(m):
      return np.log(npla.det(m))
    (psi, dof) = self.__parse_args__(args)
    p = len(psi)
    log_density = 0.5 * dof * (logdet(psi) - p * np.log(2)) \
      - spsp.multigammaln(0.5 * dof, p) \
      - 0.5 * (dof + p + 1) * logdet(x) \
      - 0.5 * np.trace(np.dot(psi, npla.inv(x)))
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
      A = args.np_prng().normal(size=(p, int(dof)))
    else:
      # https://en.wikipedia.org/wiki/Wishart_distribution#Bartlett_decomposition
      A = np.diag(np.sqrt(args.np_prng().chisquare(dof - np.arange(p), size=p)))
      A[np.tril_indices_from(A,-1)] = args.np_prng().normal(size=(p*(p-1)//2))
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
  def simulateNumeric(self, params, np_rng):
    mu, sigma = params
    return np_rng.normal(loc=mu, scale=sigma)

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
      raise Exception("Cannot rejection auto-bound psp with unbounded likelihood")

  def simulate(self, args):
    return self.simulateNumeric(args.operandValues(), args.np_prng())

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
    return args.np_prng().normal(*args.operandValues())

  def logDensity(self, x, args):
    return sum(scipy.stats.norm.logpdf(x, *args.operandValues()))

  def gradientOfLogDensity(self,x,args):
    (mu, sigma) = args.operandValues()
    gradX = -(x - mu) / (np.power(sigma,2))
    gradMu = (x - mu) / (np.power(sigma,2))
    gradSigma = (np.power(x - mu,2) - np.power(sigma,2)) / np.power(sigma,3)
    return (gradX,[gradMu,gradSigma])

  def description(self,name):
    return "  %s(mu, sigma) samples a vector of normal variates with means mu "\
      "and corresponding standard deviations sigma." % name


# These two only differ because the gradients need to account for broadcasting
class NormalsvOutputPSP(RandomPSP):
  def simulate(self, args):
    return args.np_prng().normal(*args.operandValues())

  def logDensity(self, x, args):
    return sum(scipy.stats.norm.logpdf(x, *args.operandValues()))

  def gradientOfLogDensity(self, x, args):
    (mu, sigma) = args.operandValues()
    x = np.array(x); sigma = np.array(sigma)
    gradX = -(x - mu) / (np.power(sigma,2))
    gradMu = (x - mu) / (np.power(sigma,2))
    gradSigma = (np.power(x - mu,2) - np.power(sigma,2)) / np.power(sigma,3)
    return (gradX,[sum(gradMu),gradSigma])

  def description(self,name):
    return "  %s(mu, sigma) samples a vector of normal variates, all with the "\
      "same mean mu, and a vector of standard deviations sigma." % name


class NormalvsOutputPSP(RandomPSP):
  def simulate(self, args):
    return args.np_prng().normal(*args.operandValues())

  def logDensity(self, x, args):
    return sum(scipy.stats.norm.logpdf(x, *args.operandValues()))

  def gradientOfLogDensity(self, x, args):
    (mu, sigma) = args.operandValues()
    x = np.array(x); mu = np.array(mu)
    gradX = -(x - mu) / (np.power(sigma,2))
    gradMu = (x - mu) / (np.power(sigma,2))
    gradSigma = (np.power(x - mu,2) - np.power(sigma,2)) / np.power(sigma,3)
    return (gradX,[gradMu,sum(gradSigma)])

  def logDensityBound(self, x, args):
    (mu, sigma) = args.operandValues()
    if sigma is not None:
      # I need to know the length
      N = None
      if x is not None:
        N = len(x)
      elif mu is not None:
        N = len(mu)
      else:
        # XXX Perhaps modify the rejection mechanism to supply more
        # type information, so I can get the length (which has to be
        # fixed for these density bounds to be comparable anyway).
        raise Exception("Cannot rejection auto-bound vector Gaussian of unknown length")
      return -(math.log(sigma) + HALF_LOG2PI) * N
    elif x is not None and mu is not None:
      if len(x) == len(mu):
        raise Exception("TODO: Compute the log density bound for vector Gaussian with known mean and observation and unknown shared sigma")
      else:
        return float("-inf")
    else:
      raise Exception("Cannot rejection auto-bound psp with unbounded likelihood")

  def description(self,name):
    return "  %s(mu, sigma) samples a vector of normal variates, with a "\
      "a vector of means mu, and all the same standard deviation sigma." % name

registerBuiltinSP("normalss", typed_nr(NormalOutputPSP(),
    [t.NumberType(), t.NumberType()], t.NumberType()))

registerBuiltinSP("normalsv", typed_nr(NormalsvOutputPSP(),
    [t.NumberType(), t.ArrayUnboxedType(t.NumberType())],
     t.ArrayUnboxedType(t.NumberType())))

registerBuiltinSP("normalvs", typed_nr(NormalvsOutputPSP(),
    [t.ArrayUnboxedType(t.NumberType()), t.NumberType()],
     t.ArrayUnboxedType(t.NumberType())))

registerBuiltinSP("normalvv", typed_nr(NormalvvOutputPSP(),
    [t.ArrayUnboxedType(t.NumberType()), t.ArrayUnboxedType(t.NumberType())],
     t.ArrayUnboxedType(t.NumberType())))

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


class LogNormalOutputPSP(RandomPSP):
  def simulate(self, args):
    mu, sigma = args.operandValues()
    return exp(args.np_prng().normal(loc=mu, scale=sigma))

  def gradientOfSimulate(self, args, x, direction):
    # dy = dmu + (y - mu)/sigma dsigma
    #  x = e^y
    # dx = d(e^y)
    #    = e^y dy
    #    = e^y dmu + e^y (y - mu)/sigma dsigma
    #    = x dmu + x (log x - mu)/sigma dsigma
    mu, sigma = args.operandValues()
    return [direction*x, direction*(x*(log(x) - mu)/sigma)]

  def logDensity(self, x, args):
    # x = e^y, y = log x
    # log P(x) = log [P(y) dy/dx] = log [P(y) d/dx log x]
    #   = log [P(y)/x]
    #   = [-log x - log sigma - HALF_LOG2PI - (y - mu)^2/(2 sigma^2)]
    #   = [-log x - log sigma - HALF_LOG2PI - (log x - mu)^2/(2 sigma^2)]
    mu, sigma = args.operandValues()
    logx = log(x)
    deviation = logx - mu
    return -logx - log(sigma) - HALF_LOG2PI \
      - (deviation*deviation/(2*sigma*sigma))

  def logDensityBound(self, x, args):
    # d[-log x - log sigma - 0.5 log 2pi - (log x - mu)^2/(2 sigma^2)]
    # = -1/x dx - 1/sigma dsigma - d[(log x - mu)^2/(2 sigma^2)]
    # = -1/x dx - 1/sigma dsigma
    #   - [2 sigma^2 d[(log x - mu)^2] - (log x - mu)^2 d(2 sigma^2)
    #     / (2 sigma^2)^2
    # = -1/x dx - 1/sigma dsigma
    #   - [2 sigma^2 2 (log x - mu) d(log x - mu)
    #         - (log x - mu)^2 2 d(sigma^2)]
    #     / (4 sigma^4)
    # = -1/x dx - 1/sigma dsigma
    #   - [2 sigma^2 2 (log x - mu) (1/x dx - dmu)
    #         - (log x - mu)^2 2 2 sigma dsigma]
    #     / (4 sigma^4)
    # = -1/x dx - 1/sigma dsigma
    #   - [4 sigma^2 (log x - mu) (1/x dx - dmu)
    #         - 4 sigma (log x - mu)^2 dsigma]
    #     / (4 sigma^4)
    # = -1/x dx - 1/sigma dsigma
    #   - [(log x - mu) (1/x dx - dmu)
    #         - (log x - mu)^2/sigma dsigma]
    #     / sigma^2
    # = [-1/x - (log x - mu)/(sigma^2 x)] dx
    #   + (log x - mu)/sigma^2 dmu
    #   + [-1/sigma + (log x - mu)^2/sigma^3] dsigma
    #
    # Hence for fixed mu and sigma, x is critical at
    #
    #   -1/x = (log x - mu)/(sigma^2 x),
    #
    # or
    mu, sigma = args.operandValues()
    if mu is not None and sigma is not None:
      assert x is None
      # Density is critical at
      #
      #         0 = -1/x - (log x - mu)/(sigma^2 x)
      #         -1/x = (log x - mu)/(sigma^2 x)
      #         -1 = (log x - mu)/sigma^2
      #         -sigma^2 = log x - mu
      #         mu - sigma^2 = log x
      #         x = e^{mu - sigma^2}.
      #
      return sigma**2/2 - mu - log(sigma) - HALF_LOG2PI
    elif x is not None and sigma is not None:
      assert mu is None
      # Density is critical at
      #
      #         0 = (log x - mu)/sigma^2
      #         mu = log x.
      #
      return -log(x) - log(sigma) - HALF_LOG2PI
    elif x is not None and mu is not None:
      assert sigma is None
      # Density is critical at
      #
      #         0 = -1/sigma + (log x - mu)^2/sigma^3
      #         1/sigma = (log x - mu)^2/sigma^3
      #         1 = (log x - mu)^2/sigma^2
      #         sigma^2 = (log x - mu)^2
      #         sigma = |log x - mu|.
      #
      logx = log(x)
      return -logx - log(abs(logx - mu)) - HALF_LOG2PI - (1/2)
    else:
      raise NotImplementedError(
        'This bivariate optimization left as an exercise for the reader.')

  def gradientOfLogDensity(self, x, args):
    raise NotImplementedError('My support is bounded!  Bad for gradients.')

  def description(self, name):
    return '  %s(mu, sigma) samples a normal distribution with mean mu' \
      ' and standard deviation sigma, and yields its exponential.' % (name,)


registerBuiltinSP('lognormal', typed_nr(LogNormalOutputPSP(),
    [t.NumberType(), t.PositiveType()], t.PositiveType()))


class VonMisesOutputPSP(RandomPSP):
  def simulate(self, args):
    (mu, kappa) = args.operandValues()
    return args.np_prng().vonmises(mu=mu, kappa=kappa)

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
      raise Exception("Cannot rejection auto-bound psp with unbounded likelihood")

  def gradientOfLogDensity(self, x, args):
    (mu, kappa) = args.operandValues()
    gradX  = -math.sin(x - mu) * kappa
    gradMu = math.sin(x - mu) * kappa
    # d/dk(log density) = cos(x-mu) - [2pi d(I_0)(k)]/2pi I_0(k)
    # d/dk I_0(k) = I_1(k)
    gradK  = math.cos(x - mu) - (spsp.i1(kappa) / spsp.i0(kappa))
    return (gradX, [gradMu, gradK])

  def description(self,name):
    return "  %s(mu, kappa) samples a von Mises distribution with mean mu and "\
      "shape kappa. The output is normalized to the interval [-pi,pi]." % name


registerBuiltinSP("vonmises", typed_nr(VonMisesOutputPSP(),
  [t.NumberType(), t.PositiveType()], t.NumberType()))


class UniformOutputPSP(RandomPSP):
  # TODO don't need to be class methods
  def simulateNumeric(self, low, high, np_rng):
    return np_rng.uniform(low=low, high=high)

  def logDensityNumeric(self, x, low, high):
    return scipy.stats.uniform.logpdf(x, low, high-low)

  def logDensityBoundNumeric(self, _, low, high):
    if low is None or high is None:
      # Unbounded
      raise Exception("Cannot rejection auto-bound psp with unbounded likelihood")
    else:
      return -math.log(high - low)

  def simulate(self, args):
    return self.simulateNumeric(*(args.operandValues() +
                                  [args.np_prng()]))

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


class LogOddsUniformOutputPSP(RandomPSP):
  def simulate(self, args):
    return logit(args.np_prng().uniform())

  def logDensity(self, x, _args):
    # If Y ~ U[0,1] and X = logit(Y), then Y = logistic(X), so that
    # since P_Y(y) = 1, we have the change of variables density
    #
    #   P_X(x) = P_Y(logistic(x))*logistic'(x) = 1*logistic'(x)
    #          = logistic'(x).
    #
    # Hence log P(x) = log logistic'(x).
    #
    return log_d_logistic(x)

  def gradientOfLogDensity(self, x, _args):
    # Let L(x) = logistic(x).  We need
    #
    #   d/dx log P(x) = d/dx log L'(x)
    #     = (log o L')'(x) = log'(L'(x)) L''(x)
    #     = L''(x)/L'(x).
    #
    # Note that L' = L*(1 - L), so
    #
    #   L'' = (L*(1 - L))' = L'*(1 - L) + L*(1 - L)'
    #     = L'*(1 - L) - L*L';
    #
    # hence L''/L' = (1 - L) - L = 1 - 2 L.
    #
    return 1 - 2*logistic(x), []

  def logDensityBound(self, _x, _args):
    # Any maximum of log P(x) is a zero of d/dx log P(x) = 1 - 2 L(x),
    # where L(x) is the logistic function; hence if x is maximum then
    # L(x) = 1/(1 + e^{-x}) = 1/2, so that x = 0.  The maximum value
    # is
    #
    #   log P(0) = log L'(0) = log (1 - L(0)) L(0)
    #     = log (1 - 1/2)*(1/2) = log (1/4)
    #     = -log 4.
    #
    return -log(4)

  def description(self, name):
    return "  %s() samples a log-odds representation of a uniform real number"\
      " between 0 and 1.  This is also called the \"logistic distribution\","\
      " named differently to avoid confusion with the logistic function."\
      % (name,)


registerBuiltinSP("log_odds_uniform", typed_nr(LogOddsUniformOutputPSP(),
  [], t.NumberType()))


class BetaOutputPSP(RandomPSP):
  # TODO don't need to be class methods
  def simulateNumeric(self, params, np_rng):
    alpha, beta = params

    # Beta(0, 0) is a pair of Dirac deltas at 0 and 1.  Beta(0, b) is
    # a Dirac delta at 1; Beta(a, 0) is a Dirac delta at 0.  For any a
    # or b rounded to zero, this is the best we can do.
    if alpha == 0 and beta == 0:
      return float(np_rng.randint(2))
    elif alpha == 0:
      return 1.
    elif beta == 0:
      return 0.
    elif min(alpha, beta) < 1e-300:
      # Not a delta -- but close enough to it at 0 that no matter what
      # beta is, the spike near 1 would always be rounded to 1 in
      # practice.
      #
      # XXX This is probably true for alpha < 1e-300.  I am not so
      # sure that for beta < 1e-300, the spike near 0 would always be
      # rounded to 0 in practice -- there are many more floating-point
      # numbers near 0 than there are near 1.  But if you really care
      # about the accuracy of the *distribution* in this case, maybe
      # you should rethink your model.  We do this case to avoid the
      # much more significant problem of giving NaN in some cases,
      # described below.
      return 0. if np_rng.uniform() < alpha/(alpha + beta) else 1.

    if 1 < alpha or 1 < beta:
      # Easy case: at least one of the pseudocounts exceeds 1.  Use
      # the well-known relation to independent Gamma distributions:
      # for independent G ~ Gamma(alpha) and H ~ Gamma(beta), we have
      # G/(G + H) ~ Beta(alpha, beta).
      G = np_rng.gamma(shape=alpha)
      H = np_rng.gamma(shape=beta)
      return G/(G + H)

    # Johnk's algorithm: Given u, v uniform on [0, 1], let x =
    # u^(1/alpha) and y = v^(1/beta); if x + y <= 1, yield x/(x + y),
    # as described in
    #
    #   Luc Devroye, _Nonuniform Random Variate Generation_,
    #   Springer-Verlag, 1986, Ch. IX `Continuous univariate
    #   densities', Sec. 3.5 'Johnk's theorem and its implications',
    #   p. 416.
    #
    # (Original paper by M.D. Johnk, cited by Devroye, is in German.)
    while True:
      u = np_rng.uniform()
      v = np_rng.uniform()
      x = u**(1/alpha)
      y = v**(1/beta)
      if 1 < x + y:
          continue            # reject

      # If u, v, alpha, and beta are far enough from zero that x and
      # y are not rounded to zero, do the division in direct space.
      if 0 < x + y:
        return x/(x + y)

      # Otherwise, do the division in log space:
      #
      #       x/(x + y) = exp log x/(x + y)
      #       = exp [log x - log (x + y)]
      #       = exp [log x - log m*(x/m + y/m)]
      #       = exp [log x - log m - log (x/m + y/m)]
      #       = exp [log x - log m - log (exp log x/m + exp log y/m)]
      #       = exp [log x - log m
      #               - log (exp (log x - log m) + exp (log y - log m))]
      #       = exp [log x' - log (exp log x' + exp log y')]
      #
      # where m = max(x, y), x' = x/m, and y' = y/m, in order to
      # avoid overflow in the intermediate exp.
      #
      # Should we worry about zero u or v?
      #
      # Numbers from 0 to the smallest positive floating-point
      # number, or the slightly larger smallest positive /normal/
      # floating-point number if the CPU is in the nonstandard but
      # common faster flush-to-zero mode, will be rounded to zero.
      # The smallest positive normal floating-point number is
      # 2^-1022.  Hence
      #
      #       Pr[u = 0 or v = 0]
      #         = Pr[u = 0] + Pr[v = 0] - Pr[u = 0 and v = 0]
      #        <= 2^-1022 + 2^-1022 - 2^-2044
      #         = 2^-1021 - 2^-2044
      #         < 2^-1021 <<< 2^-256.
      #
      # This will never happen unless the PRNG is broken.
      #
      # XXX Is numpy's PRNG broken?  Unclear: many alleged `uniform
      # [0, 1]' samplers actually give probability 2^-64 or 2^-53 of
      # yielding zero, e.g. by drawing an integer in {0, 1, 2, ...,
      # 2^53 - 1} and dividing by 2^53.  This is not what numpy's PRNG
      # does but it's not too far off either.

      assert 0 < u
      assert 0 < v
      log_x = np.log(u)/alpha
      log_y = np.log(v)/beta

      # Should we worry about floating-point overflow of log_x (and
      # respectively log_y) to -infinity when alpha (resp. beta) is
      # very small so that 1/alpha or (resp. 1/beta) is very large?
      # That would cause the log-sum-exp calculation to yield NaN
      # instead of a real number in [0, 1], which would be bad.
      #
      # The least value attained by log(u) is just over -745, when u
      # is the smallest nonnegative floating-point number 2^-1074.  In
      # this case, there is no overflow for any alpha above 1e-305:
      # log(u)/alpha <= -745/1e-305 = -8e2 * 1e305 = -8e307, which
      # does not overflow since the largest finite floating-point
      # magnitude is a little over 1e308.
      #
      # Since we round the Beta(alpha, beta) distribution to
      # Bernoulli-weighted spikes at 0 and 1 when alpha or beta is
      # below 1e-300, this does not concern us for any possible values
      # of u and v.

      assert not np.isinf(log_x)
      assert not np.isinf(log_y)

      log_m = max(log_x, log_y)
      log_x -= log_m
      log_y -= log_m
      return np.exp(log_x - np.log(np.exp(log_x) + np.exp(log_y)))

  def logDensityNumeric(self, x, params):
    return scipy.stats.beta.logpdf(x,*params)

  def simulate(self, args):
    return self.simulateNumeric(args.operandValues(), args.np_prng())

  def logDensity(self, x, args):
    return self.logDensityNumeric(x,args.operandValues())

  def gradientOfLogDensity(self, x, args):
    (alpha, beta) = args.operandValues()
    gradX = ((float(alpha) - 1) / x) - ((float(beta) - 1) / (1 - x))
    gradAlpha = spsp.digamma(alpha + beta) - spsp.digamma(alpha) + math.log(x)
    gradBeta = spsp.digamma(alpha + beta) - spsp.digamma(beta) + math.log1p(-x)
    return (gradX,[gradAlpha,gradBeta])

  def description(self, name):
    return "  %s(alpha, beta) returns a sample from a Beta distribution with "\
      "shape parameters alpha and beta." % name

  # TODO Beta presumably has a variational kernel too?


registerBuiltinSP("beta", typed_nr(BetaOutputPSP(),
  [t.PositiveType(), t.PositiveType()], t.ProbabilityType()))


class LogBetaOutputPSP(RandomPSP):
  def simulate(self, args):
    np_rng = args.np_prng()
    alpha, beta = args.operandValues()

    # . log Beta(0, 0) is a pair of Dirac deltas at -inf and 0.
    # . log Beta(0, b) is a Dirac delta at -inf.
    # . log Beta(a, 0) is a Dirac delta at 0.
    #
    # For any a or b rounded to zero, this is the best we can do.
    #
    inf = float('inf')
    if alpha == 0 and beta == 0:
      return -inf if np_rng.randint(2) else 0
    elif alpha == 0:
      return -inf
    elif beta == 0:
      return 0
    elif min(alpha, beta) < 1e-300:
      # Avoid NaNs due to duelling infinities from log Gamma samples
      # with shape below 1e-300.  If alpha and beta both exceed
      # 1e-300, the log Gamma sampler never overflows.
      #
      return 0 if np_rng.uniform() < alpha/(alpha + beta) else -inf

    # Given independent G ~ Gamma(alpha) and H ~ Gamma(beta), the
    # well-known identity G/(G + H) ~ Beta(alpha, beta) lets us sample
    # from the Beta distribution.  We want log G/(G + H).  If alpha or
    # beta is small, G and H may be rounded to zero, whereas we can
    # sample log G and log H without overflowing to -infinity,
    # provided alpha and beta are at least 1e-300, and then we can
    # compute log G - log (e^{log G} + e^{log H}).
    #
    log_G = simulateLogGamma(alpha, np_rng)
    log_H = simulateLogGamma(beta, np_rng)
    assert not math.isinf(log_G)
    assert not math.isinf(log_H)
    return log_G - logsumexp([log_G, log_H])

  def logDensity(self, x, args):
    # x = log y for a beta sample y, so its density is the beta
    # density of y = e^x with the Jacobian dy/dx = e^x:
    #
    #   log p(x | a, b) = log [p(y | a, b) dy/dx]
    #   = (a - 1) log y + (b - 1) log (1 - y) - log Beta(a, b) + log dy/dx
    #   = (a - 1) log e^x + (b - 1) log (1 - e^x) - log B(a, b) + log e^x
    #   = (a - 1) x + (b - 1) log (1 - e^x) - log B(a, b) + x
    #   = a x + (b - 1) log (1 - e^x) - log B(a, b).
    #
    a, b = args.operandValues()
    return a*x + (b - 1)*log1p(-exp(x)) - scipy.special.betaln(a, b)

  def gradientOfLogDensity(self, x, args):
    # We seek the derivative of
    #
    #   L = log p(x | a, b) = a x + (b - 1) log (1 - e^x) - log B(a, b).
    #
    # Note that log1p'(x) = 1/(1 + x), so that
    #
    #   d/dx log (1 - e^x) = d/dx log1p(-e^x)
    #     = (log1p o (-exp))'(x)
    #     = log1p'(-exp(x)) * (-exp'(x))
    #     = (1/(1 - e^x)) * (-e^x)
    #     = -e^x/(1 - e^x)
    #     = -[e^x e^-x]/[(1 - e^x) e^-x]
    #     = -1/(e^-x - 1).
    #
    # Hence we have:
    #
    #   dL/dx = a - (b - 1)/(e^-x - 1)
    #   dL/da = x - d/da log B(a, b)
    #   dL/db = log (1 - e^x) - d/db log B(a, b).
    #
    # For the last terms, note that B(a, b) is symmetric in a, b; that
    # B(a, b) = Gamma(a) Gamma(b) / Gamma(a + b); and that the digamma
    # function F(x) = d/dx log Gamma(x).  Hence
    #
    #   d/da log B(a, b) = d/da log Gamma(a) Gamma(b) / Gamma(a + b)
    #     = d/da [log Gamma(a) + log Gamma(b) - log Gamma(a + b)]
    #     = d/da log Gamma(a) + d/da log Gamma(b) - d/da log Gamma(a + b)
    #     = d/da log Gamma(a) - d/da log Gamma(a + b)
    #     = F(a) - F(a + b),
    #
    # and likewise, by symmetry, d/db log B(a, b) = F(b) - F(a + b).
    #
    a, b = args.operandValues()
    d_x = a - (b - 1)/expm1(-x)
    d_a = x + spsp.digamma(a + b) - spsp.digamma(a)
    d_b = log(-expm1(x)) + spsp.digamma(a + b) - spsp.digamma(b)
    return (d_x, [d_a, d_b])

  def description(self, name):
    return "  %s(alpha, beta) returns the log-space representation of a" \
      " sample from a Beta distribution" \
      " with shape parameters alpha and beta." \
      % (name,)


registerBuiltinSP("log_beta", typed_nr(LogBetaOutputPSP(),
  [t.PositiveType(), t.PositiveType()], t.NumberType()))


class LogOddsBetaOutputPSP(RandomPSP):
  def simulate(self, args):
    np_rng = args.np_prng()
    alpha, beta = args.operandValues()

    # logit Beta(0, 0) is a pair of Dirac deltas at -inf and +inf.
    # logit Beta(0, b) is a Dirac delta at -inf; logit Beta(a, 0) is a
    # Dirac delta at +inf.  For any a or b rounded to zero, this is
    # the best we can do.
    #
    inf = float('inf')
    if alpha == 0 and beta == 0:
      return -inf if np_rng.randint(2) else +inf
    elif alpha == 0:
      return -inf
    elif beta == 0:
      return +inf
    elif min(alpha, beta) < 1e-300:
      # Avoid NaNs due to duelling infinities from log Gamma samples
      # with shape below 1e-300.  If alpha and beta both exceed
      # 1e-300, the log Gamma sampler never overflows.
      return +inf if np_rng.random() < alpha/(alpha + beta) else -inf

    # For independent G ~ Gamma(alpha) and H ~ Gamma(beta), we have
    # the well-known identity G/(G + H) ~ Beta(alpha, beta).  To
    # compute the logit of this, note that
    #
    #                             G/(G + H)
    #   logit(G/(G + H)) = log ---------------
    #                           1 - G/(G + H)
    #
    #                     G
    #   = log -------------------------
    #          (G + H)*[1 - G/(G + H)]
    #
    #                    G
    #   = log ---------------------------
    #          G + H - G*(G + H)/(G + H)
    #
    #              G
    #   = log ----------- = log (G/H) = log G - log H.
    #          G + H - G
    #
    if min(alpha, beta) < 1:
      # We can't sample Gamma(shape) accurately because samples will
      # be rounded to zero, but we can sample log Gamma(shape) without
      # overflowing to -infinity.  So yield the difference of log
      # Gamma samples.
      #
      # The danger of catastrophic cancellation is small even if
      # alpha = beta because for Gamma(shape), the mean is shape and
      # the standard deviation is sqrt(shape), so that the spread is
      # very wide relative to the magnitude of the mean.
      #
      log_G = simulateLogGamma(alpha, np_rng)
      log_H = simulateLogGamma(beta, np_rng)
      assert not math.isinf(log_G)
      assert not math.isinf(log_H)
      return log_G - log_H

    else:       # 1 <= min(alpha, beta)
      # If alpha and beta are large and close to one another, then
      # log G and log H will also usually be close, so that their
      # difference will exhibit catastrophic cancellation.
      #
      # Fortunately, they will never be rounded to zero -- the CDF
      # of Gamma(shape=1) at 1e-300 is about 1e-300 <<< 2^-256, and
      # larger shapes give even smaller probabilities for small
      # values.  So we can always divide and log.
      #
      G = np_rng.gamma(alpha)
      H = np_rng.gamma(beta)
      assert G != 0
      assert H != 0
      return log(G/H)

  def logDensity(self, x, args):
    # x = logit(y) for a beta sample y, so its density is the beta
    # density of y = logistic(x) with the Jacobian dy/dx =
    # logistic'(x) = logistic(x) logistic(-x):
    #
    #   log p(x | a, b) = log [p(y | a, b) dy/dx]
    #   = (a - 1) log y + (b - 1) log (1 - y) - log Beta(a, b) + log dy/dx
    #   = (a - 1) log logistic(x)
    #       + (b - 1) log (1 - logistic(x))
    #       - log Beta(a, b)
    #       + log logistic'(x)
    #   = (a - 1) log logistic(x) + (b - 1) log logistic(-x)
    #       - log Beta(a, b)
    #       + log [logistic(x) logistic(-x)]
    #   = a log logistic(x) - log logistic(x)
    #       + b log logistic(-x) - log logistic(-x)
    #       - log Beta(a, b)
    #       + log logistic(x) + log logistic(-x)
    #   = a log logistic(x) + b log logistic(-x) - log Beta(a, b).
    #
    a, b = args.operandValues()
    return a*log_logistic(x) + b*log_logistic(-x) - betaln(a, b)

  def gradientOfLogDensity(self, x, args):
    # We seek the derivative of
    #
    #   L = log p(x | a, b)
    #     = a log logistic(x) + b log logistic(-x) - log Beta(a, b)
    #
    # with respect to x, and b.  Note that
    #
    #   d/dx log logistic(x) = logistic(-x).
    #
    # Hence
    #
    #   dL/dx = a logistic(-x) - b logistic(x),
    #   dL/da = log logistic(x) - d/da log B(a, b), and
    #   dL/db = log logistic(-x) - d/db log B(a, b).
    #
    # For the last terms, note that B(a, b) is symmetric in a, b; that
    # B(a, b) = Gamma(a) Gamma(b) / Gamma(a + b); and that the digamma
    # function F(x) = d/dx log Gamma(x).  Hence
    #
    #   d/da log B(a, b) = d/da log Gamma(a) Gamma(b) / Gamma(a + b)
    #     = d/da [log Gamma(a) + log Gamma(b) - log Gamma(a + b)]
    #     = d/da log Gamma(a) + d/da log Gamma(b) - d/da log Gamma(a + b)
    #     = d/da log Gamma(a) - d/da log Gamma(a + b)
    #     = F(a) - F(a + b),
    #
    # and likewise, by symmetry, d/db log B(a, b) = F(b) - F(a + b).
    #
    a, b = args.operandValues()
    d_x = a*logistic(-x) - b*logistic(x)
    d_a = log_logistic(x) + digamma(a + b) - digamma(a)
    d_b = log_logistic(-x) + digamma(a + b) - digamma(b)
    return (d_x, [d_a, d_b])

  def description(self, name):
    return "  %s(alpha, beta) returns the log-odds representation" \
      " of a sample from a Beta distribution" \
      " with shape parameters alpha and beta." \
      % (name,)


registerBuiltinSP("log_odds_beta", typed_nr(LogOddsBetaOutputPSP(),
  [t.PositiveType(), t.PositiveType()], t.NumberType()))


class ExponOutputPSP(RandomPSP):
  # TODO don't need to be class methods
  def simulateNumeric(self, theta, np_rng):
    return np_rng.exponential(scale=1.0/theta)

  def logDensityNumeric(self, x, theta):
    return scipy.stats.expon.logpdf(x,scale=1.0/theta)

  def simulate(self,args):
    return self.simulateNumeric(*(args.operandValues() +
                                  [args.np_prng()]))

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
  def simulateNumeric(self, alpha, beta, np_rng):
    return np_rng.gamma(shape=alpha, scale=1.0/beta)

  def logDensityNumeric(self, x, alpha, beta):
    return scipy.stats.gamma.logpdf(x, alpha, scale=1.0/beta)

  def simulate(self, args):
    return self.simulateNumeric(*(args.operandValues() +
                                  [args.np_prng()]))

  def gradientOfSimulate(self, args, value, direction):
    # These gradients were computed by Sympy; the script to get them
    # is in doc/gradients.py.  Subsequently modified to convert
    # math.log(math.exp(foo)) to (foo), because apparently Sympy's
    # simplifier is not up to that.
    alpha, beta = args.operandValues()
    if alpha == 1:
      warnstr = ('Gradient of simulate is discontinuous at alpha = 1.\n'
                 'Issue https://app.asana.com/0/11192551635048/14271708124534.')
      warnings.warn(warnstr, GradientWarning)
      gradAlpha = 0
      gradBeta = -value / math.pow(beta, 2.0)
    elif alpha > 1:
      x0 = value / (3.0 * alpha - 1)
      gradAlpha = (-3. * x0 / 2. + 3. * 3. ** (2. / 3.) *
                   (beta * x0) ** (2. / 3.) / (2. * beta))
      gradBeta = -value / beta
    else:
      if value <= (1.0 / beta) * math.pow(1 - alpha, 1.0 / alpha):
        x0 = (beta * value) ** alpha
        gradAlpha = -x0 ** (1.0 / alpha) * math.log(x0) / (alpha ** 2.0 * beta)
        gradBeta = -((beta * value) ** alpha) ** (1.0 / alpha) / beta ** 2.0
      else:
        x0 = -alpha + 1
        x1 = 1.0 / alpha
        x2 = alpha * (x1 * (x0 - (beta * value) ** alpha))
        x3 = -x2
        x4 = x0 + x3
        gradAlpha = (x4 ** (x0 * x1) * (x3 + (alpha + x2 - 1) *
                     math.log(x4)) / (alpha ** 2.0 * beta))
        x0 = 1.0 / alpha
        gradBeta = ( -(-alpha * (-x0 * (alpha +
          (beta * value) ** alpha - 1)) - alpha + 1) ** x0 / beta ** 2.0 )
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
  def simulateNumeric(self, nu, loc, scale, np_rng):
    return loc + scale*np_rng.standard_t(df=nu)

  def logDensityNumeric(self, x, nu, loc, scale):
    return scipy.stats.t.logpdf(x,nu,loc,scale)

  def simulate(self, args):
    vals = args.operandValues()
    loc = vals[1] if len(vals) > 1 else 0
    shape = vals[2] if len(vals) > 1 else 1
    return self.simulateNumeric(vals[0],loc,shape,args.np_prng())

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
                               + spsp.digamma(x5 + 1. / 2.)) - x2
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
  def simulateNumeric(self, a, b, np_rng):
    return 1./np_rng.gamma(shape=a, scale=1./b)

  def logDensityNumeric(self, x, a, b):
    return scipy.stats.invgamma.logpdf(x, a, scale=b)

  def simulate(self, args):
    return self.simulateNumeric(*(args.operandValues() +
                                  [args.np_prng()]))

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
  def simulateNumeric(self, a, b, np_rng):
    return np_rng.laplace(loc=a, scale=b)

  def logDensityNumeric(self, x, a, b):
    return scipy.stats.laplace.logpdf(x,a,b)

  def simulate(self, args):
    return self.simulateNumeric(*(args.operandValues() +
                                  [args.np_prng()]))

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

  def incorporate(self, value):
    self.ctN += 1
    self.xsum += value
    self.xsumsq += value * value

  def unincorporate(self, value):
    self.ctN -= 1
    self.xsum -= value
    self.xsumsq -= value * value

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
    args.spaux().incorporate(value)

  def unincorporate(self, value, args):
    args.spaux().unincorporate(value)

  def simulate(self, args):
    return args.np_prng().normal(loc=self.mu, scale=self.sigma)

  def logDensity(self, value, _args):
    return scipy.stats.norm.logpdf(value, loc=self.mu, scale=self.sigma)

  def logDensityOfData(self, aux):
    return SuffNormalOutputPSP.logDensityOfDataNumeric(aux, self.mu, self.sigma)

  @staticmethod
  def logDensityOfDataNumeric(aux, mu, sigma):
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
    args.spaux().incorporate(value)

  def unincorporate(self, value, args):
    args.spaux().unincorporate(value)

  def updatedParams(self, aux):
    return CNigNormalOutputPSP.posteriorHypersNumeric \
      ((self.m, self.V, self.a, self.b), aux.cts())

  def simulate(self, args):
    # Posterior predictive is Student's t (206)
    (mn, Vn, an, bn) = self.updatedParams(args.spaux())
    loc = mn
    scale = math.sqrt(bn/an*(1 + Vn))
    df = 2*an
    return loc + scale*args.np_prng().standard_t(df=df)

  def logDensity(self, value, args):
    (mn, Vn, an, bn) = self.updatedParams(args.spaux())
    return scipy.stats.t.logpdf(value, 2*an, loc=mn,
      scale=math.sqrt(bn/an*(1+Vn)))

  def logDensityOfData(self, aux):
    # Marginal likelihood of the data (203)
    [ctN, xsum, xsumsq] = aux.cts()
    (mn, Vn, an, bn) = self.updatedParams(aux)
    term1 = 0.5 * math.log(abs(Vn)) - 0.5 * math.log(abs(self.V))
    term2 = self.a * math.log(self.b) - an * math.log(bn)
    term3 = spsp.gammaln(an) - spsp.gammaln(self.a)
    term4 = math.log(1) - ctN/2. * math.log(math.pi) - ctN * math.log(2)
    return term1 + term2 + term3 + term4

  @staticmethod
  def posteriorHypersNumeric(prior_hypers, counts):
    # http://www.cs.ubc.ca/~murphyk/Papers/bayesGauss.pdf#page=16
    # (197 - 200)
    [m, V, a, b] = prior_hypers
    [ctN, xsum, xsumsq] = counts
    Vn = 1 / (1.0/V + ctN)
    mn = Vn*(1.0/V*m + xsum)
    an = a + ctN / 2.0
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
    return UNigNormalAAALKernel(self)

  def simulate(self, args):
    return MakerUNigNormalOutputPSP.simulateStatic(args.np_prng(),
                                                   args.operandValues())

  @staticmethod
  def simulateStatic(np_rng, hypers, spaux=None):
    (m, V, a, b) = hypers
    # Simulate the mean and variance from NormalInverseGamma.
    # https://en.wikipedia.org/wiki/Normal-inverse-gamma_distribution#Generating_normal-inverse-gamma_random_variates
    sigma2 = 1./np_rng.gamma(shape=a, scale=1./b)
    mu = np_rng.normal(loc=m, scale=math.sqrt(sigma2*V))
    output = TypedPSP(UNigNormalOutputPSP(mu, math.sqrt(sigma2)),
      SPType([], t.NumberType()))
    return VentureSPRecord(SuffNormalSP(NullRequestPSP(), output), spaux)

  def logDensity(self, value, args):
    assert isinstance(value, VentureSPRecord)
    assert isinstance(value.sp, SuffNormalSP)
    (m, V, a, b) = args.operandValues()
    mu = value.sp.outputPSP.psp.mu
    sigma2 = value.sp.outputPSP.psp.sigma**2
    return scipy.stats.invgamma.logpdf(sigma2, a, scale=b) + \
      scipy.stats.norm.logpdf(mu, loc=m, scale=math.sqrt(sigma2*V))

  def marginalLogDensityOfData(self, aux, args):
    (m, V, a, b) = args.operandValues()
    return CNigNormalOutputPSP(m, V, a, b).logDensityOfData(aux)

  def description(self, name):
    return '  %s(alpha, beta) returns an uncollapsed Normal-InverseGamma '\
      'Normal sampler.' % name


class UNigNormalAAALKernel(PosteriorAAALKernel):
  def simulate(self, _trace, args):
    madeaux = args.madeSPAux()
    post_hypers = CNigNormalOutputPSP.posteriorHypersNumeric \
      (args.operandValues(), madeaux.cts())
    return MakerUNigNormalOutputPSP.simulateStatic(args.np_prng(),
                                                   post_hypers, spaux=madeaux)


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

  def gradientOfLogDensityOfData(self, aux, args):
    """The derivatives with respect to the args of the log density of the counts
    collected by the made SP."""
    # See the derivation in doc/sp-math/
    (mu, sigma) = args.operandValues()
    [ctN, xsum, xsumsq] = aux.cts()
    xsumsq_dev = xsumsq - 2*mu*xsum + ctN*mu**2
    grad_mu =  (xsum - ctN*mu) / sigma**2
    grad_sigma = -ctN / sigma + xsumsq_dev / sigma**3
    return [grad_mu, grad_sigma]

  def madeSpLogDensityOfDataBound(self, aux):
    [ctN, xsum, xsumsq] = aux.cts()
    if ctN == 0:
      return 0
    mu_hat = xsum / ctN
    sigma_hat = math.sqrt(xsumsq / ctN - xsum ** 2 / ctN ** 2)
    return SuffNormalOutputPSP.logDensityOfDataNumeric(aux, mu_hat, sigma_hat)

registerBuiltinSP("make_suff_stat_normal", typed_nr(MakerSuffNormalOutputPSP(),
  [t.NumberType(), t.PositiveType()], SPType([], t.NumberType())))

### References

# [1] Murphy, Kevin P. "Machine Learning, A Probabilistic
# Perspective", MIT Press, 2012. Third printing. ISBN
# 978-0-262-01802-9
