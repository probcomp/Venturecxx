import scipy.stats
import math
import numpy.random as npr
import numpy.linalg as npla
import scipy.special as spsp
import numpy as np
from utils import logDensityMVNormal, numpy_force_number
from utils import override
from exception import VentureValueError, GradientWarning
import warnings

# For some reason, pylint can never find numpy members (presumably metaprogramming).
# pylint: disable=no-member

from psp import RandomPSP
from lkernel import LKernel

class NormalDriftKernel(LKernel):
  def __init__(self,epsilon = 0.7): self.epsilon = epsilon

  def simulate(self, _trace, oldValue, args):
    mu,sigma = args.operandValues
    nu = scipy.stats.norm.rvs(0,sigma)
    term1 = mu
    term2 = math.sqrt(1 - (self.epsilon * self.epsilon)) * (oldValue - mu)
    term3 = self.epsilon * nu
    return term1 + term2 + term3

class MVNormalRandomWalkKernel(LKernel):
  def __init__(self,epsilon = 0.7):
    self.epsilon = epsilon if epsilon is not None else 0.7

  def simulate(self,trace,oldValue,args):
    (mu, _) = MVNormalOutputPSP.__parse_args__(args)
    nu = scipy.stats.norm.rvs(0,self.epsilon,mu.shape)
    return oldValue + nu

  @override(LKernel)
  def weight(self, _trace, _newValue, _oldValue, _args):
    # log P(_newValue --> _oldValue) == log P(_oldValue --> _newValue)
    (mu, sigma) = MVNormalOutputPSP.__parse_args__(_args)
    return logDensityMVNormal(_newValue, mu, sigma)

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

  def hasDeltaKernel(self): return True
  def getDeltaKernel(self,*args): return MVNormalRandomWalkKernel(*args)

  def logDensityBound(self, x, args):
    (mu, sigma) = self.__parse_args__(args)
    if sigma is not None:
      # The maximum is obtained when x = mu
      return numpy_force_number(-.5*len(sigma)*np.log(np.pi)-.5*np.log(abs(npla.det(sigma))))
    elif x is not None and mu is not None:
      raise Exception("TODO: Find an analytical form for the maximum of the log density of MVNormal for fixed x, mu, but varying sigma")
    else:
      raise Exception("Cannot rejection sample psp with unbounded likelihood")

  def description(self,name):
    return "  (%s mean covariance) samples a vector according to the given multivariate Gaussian distribution.  It is an error if the dimensionalities of the arguments do not line up." % name

  @staticmethod
  def __parse_args__(args):
    return (np.array(args.operandValues[0]), np.array(args.operandValues[1]))

class InverseWishartPSP(RandomPSP):
  def simulate(self, args):
    (lmbda, dof) = self.__parse_args__(args)
    n = lmbda.shape[0]

    try:
      chol = np.linalg.cholesky(lmbda)
    except np.linalg.linalg.LinAlgError, e:
      raise VentureValueError(e)

    if (dof <= 81+n) and (dof == np.round(dof)):
        x = np.random.randn(dof,n)
    else:
        x = np.diag(np.sqrt(scipy.stats.chi2.rvs(dof-(np.arange(n)))))
        x[np.triu_indices_from(x,1)] = np.random.randn(n*(n-1)/2)
    R = np.linalg.qr(x,'r')
    T = scipy.linalg.solve_triangular(R.T,chol.T).T
    return np.matrix(np.dot(T,T.T))

  def logDensity(self, x, args):
    (lmbda, dof) = self.__parse_args__(args)
    p = len(lmbda)
    log_density =  dof/2*(np.log(npla.det(lmbda))-p*np.log(2))-spsp.multigammaln(dof*.5, p) \
        +(-.5*(dof+p+1))*np.log(npla.det(x))-.5*np.trace(np.dot(lmbda, npla.inv(x)))
    return log_density

  def gradientOfLogDensity(self, X, args):
    '''
    based on the following wikipedia page:
      http://en.wikipedia.org/wiki/Inverse-Wishart_distribution
      http://en.wikipedia.org/wiki/Multivariate_gamma_function
      http://en.wikipedia.org/wiki/Matrix_calculus
    '''
    (lmbda, dof) = self.__parse_args__(args)
    p = len(lmbda)
    invX = npla.inv(X)
    invLmbda = npla.inv(lmbda)
    gradX = -.5*(dof+p+1)*invX+.5*np.dot(invX, np.dot(lmbda, invX))
    gradLmbda = .5*dof*invLmbda-.5*invX
    gradDof = .5*np.log(npla.det(lmbda))-.5*np.log(npla.det(X))-.5*p*np.log(2)
    for i in range(p):
      gradDof = gradDof-.5*spsp.psi(.5*(dof-i))
    return gradX, [gradLmbda, gradDof]

  def description(self,name):
    return "  (%s scale_matrix degree_of_freedeom) samples a positive definite matrix according to the given inverse wishart distribution " % name

  def __parse_args__(self, args):
    return (np.array(args.operandValues[0]), args.operandValues[1])


class WishartPSP(RandomPSP):
  '''
    Returns a sample from the Wishart distn, conjugate prior for precision matrices.
  '''
  def simulate(self, args):
    (sigma, dof) = self.__parse_args__(args)
    n = sigma.shape[0]
    try:
      chol = np.linalg.cholesky(sigma)
    except np.linalg.linalg.LinAlgError, e:
      raise VentureValueError(e)

    # use matlab's heuristic for choosing between the two different sampling schemes
    if (dof <= 81+n) and (dof == round(dof)):
        # direct
        X = np.dot(chol,np.random.normal(size=(n,dof)))
    else:
        A = np.diag(np.sqrt(np.random.chisquare(dof - np.arange(0,n),size=n)))
        A[np.tri(n,k=-1,dtype=bool)] = np.random.normal(size=(n*(n-1)/2.))
        X = np.dot(chol,A)
    return np.matrix(np.dot(X,X.T))


  def logDensity(self, X, args):
    (sigma, dof) = self.__parse_args__(args)
    invSigma = npla.inv(sigma)
    p = len(sigma)
    log_density =  -.5*dof*(np.log(npla.det(sigma))+p*np.log(2))-spsp.multigammaln(dof*.5, p) \
          +.5*(dof-p-1)*np.log(npla.det(X))-.5*np.trace(np.dot(invSigma, X))
    return log_density

  def gradientOfLogDensity(self, X, args):
    '''
    based on the following wikipedia page:
      http://en.wikipedia.org/wiki/Inverse-Wishart_distribution
      http://en.wikipedia.org/wiki/Multivariate_gamma_function
      http://en.wikipedia.org/wiki/Matrix_calculus
    '''
    (sigma, dof) = self.__parse_args__(args)
    p = len(sigma)
    invX = npla.inv(X)
    invSigma = npla.inv(sigma)
    # print 'invSigma', invSigma
    gradX = .5*(dof-p-1)*invX-.5*invSigma
    # print 'X', X
    # print 'invX', invX
    # print 'invSigma', invSigma
    # print 'gradX', gradX
    # assert (gradX==np.transpose(gradX)).all()
    gradSigma = -.5*invSigma+.5*np.dot(invSigma, np.dot(X, invSigma))
    gradDof = .5*np.log(npla.det(X))-.5*p*np.log(2)-.5*np.log(npla.det(sigma))
    for i in range(p):
      gradDof = gradDof-.5*spsp.psi(.5*(dof-i))
    return gradX, [gradSigma, gradDof]

  def description(self,name):
    return "  (%s scale_matrix degree_of_freedeom) samples a positive definite matrix according to the given inverse wishart distribution " % name

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
  def gradientOfLogDensity(self, _, args):
    spread = 1.0/(args.operandValues[1]-args.operandValues[0])
    return (0, [spread, -spread])
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

  def gradientOfLogDensity(self,x,args):
    nu = args.operandValues[0]
    loc = args.operandValues[1] if len(args.operandValues) > 1 else 0
    shape = args.operandValues[2] if len(args.operandValues) > 1 else 1
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
    if len(args.operandValues) == 1:
      return (gradX,[gradNu])
    gradLoc = -(loc - x) * (nu + 1) / (nu * shape ** 2 + (loc - x) ** 2)
    gradShape = ((-nu * shape ** 2 + (loc - x) ** 2 * (nu + 1) -
                 (loc - x) ** 2) / (shape * (nu * shape ** 2 + (loc - x) ** 2)))
    return (gradX,[gradNu,gradLoc,gradShape])

  def description(self,name):
    return "  (%s nu loc shape) returns a sample from Student's t distribution with nu degrees of freedom, with optional location and scale parameters." % name

  # TODO StudentT presumably has a variational kernel too?

class InvGammaOutputPSP(RandomPSP):
  # TODO don't need to be class methods
  def simulateNumeric(self,a,b): return scipy.stats.invgamma.rvs(a,scale=b)
  def logDensityNumeric(self,x,a,b): return scipy.stats.invgamma.logpdf(x,a,scale=b)

  def simulate(self,args): return self.simulateNumeric(*args.operandValues)
  def logDensity(self,x,args): return self.logDensityNumeric(x,*args.operandValues)

  def gradientOfLogDensity(self,x,args):
    alpha = args.operandValues[0]
    beta = args.operandValues[1]
    gradX = (1.0 / x) * (-alpha - 1 + (beta / x))
    gradAlpha = math.log(beta) - spsp.digamma(alpha) - math.log(x)
    gradBeta = (float(alpha) / beta) - (1.0 / x)
    return (gradX,[gradAlpha,gradBeta])

  def description(self,name):
    return "(%s alpha beta) returns a sample from an inverse gamma distribution with shape parameter alpha and scale parameter beta" % name

  # TODO InvGamma presumably has a variational kernel too?

