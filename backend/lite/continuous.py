import scipy.stats
import scipy.special
import math
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
  def logDensity(self,x,args): return self.logDensityNumeric(x,args.operandValues)
  def logDensityBound(self, x, args): return self.logDensityBoundNumeric(x, *args.operandValues)

  def hasDeltaKernel(self): return False # have each gkernel control whether it is delta or not
  def getDeltaKernel(self): return NormalDriftKernel()

  def hasVariationalLKernel(self): return True
  def getParameterScopes(self): return ["REAL","POSITIVE_REAL"]

  def gradientOfLogDensity(self,x,params):
    mu = params[0]
    sigma = params[1]

    gradMu = (x - mu) / (math.pow(sigma,2))
    gradSigma = (math.pow(x - mu,2) - math.pow(sigma,2)) / math.pow(sigma,3)
    # for positive sigma, d(log density)/d(sigma) is <=> zero
    # when math.pow(x - mu,2) <=> math.pow(sigma,2) respectively
    return [gradMu,gradSigma]

  def description(self,name):
    return "(%s mu sigma) -> <number>" % name

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
  def logDensityBound(self, x, args): return self.logDensityBoundNumeric(x, *args.operandValues)

  def description(self,name):
    return "(%s low high) -> <number>" % name

  # TODO Uniform presumably has a variational kernel?

class BetaOutputPSP(RandomPSP):
  # TODO don't need to be class methods
  def simulateNumeric(self,params): return scipy.stats.beta.rvs(*params)
  def logDensityNumeric(self,x,params): return scipy.stats.beta.logpdf(x,*params)

  def simulate(self,args): return self.simulateNumeric(args.operandValues)
  def logDensity(self,x,args): return self.logDensityNumeric(x,args.operandValues)

  def description(self,name):
    return "(%s a b) -> <number>" % name

  # TODO Beta presumably has a variational kernel too?

class GammaOutputPSP(RandomPSP):
  # TODO don't need to be class methods
  def simulateNumeric(self,alpha,beta): return scipy.stats.gamma.rvs(alpha,scale=1.0/beta)
  def logDensityNumeric(self,x,alpha,beta): return scipy.stats.gamma.logpdf(x,alpha,scale=1.0/beta)

  def simulate(self,args): return self.simulateNumeric(*args.operandValues)
  def logDensity(self,x,args): return self.logDensityNumeric(x,*args.operandValues)

  def description(self,name):
    return "(%s alpha beta) -> <number>" % name

  # TODO Gamma presumably has a variational kernel too?

class StudentTOutputPSP(RandomPSP):
  # TODO don't need to be class methods
  def simulateNumeric(self,nu): return scipy.stats.t.rvs(nu)
  def logDensityNumeric(self,x,nu): return scipy.stats.t.logpdf(x,nu)

  def simulate(self,args): return self.simulateNumeric(*args.operandValues)
  def logDensity(self,x,args): return self.logDensityNumeric(x,*args.operandValues)

  def description(self,name):
    return "(%s nu) -> <number>" % name

  # TODO StudentT presumably has a variational kernel too?

