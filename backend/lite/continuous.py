import scipy.stats
import scipy.special
import math
import random
from psp import PSP,RandomPSP
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

  def simulate(self,args): return self.simulateNumeric(args.operandValues)
  def logDensity(self,x,args): return self.logDensityNumeric(x,args.operandValues)

  def hasDeltaKernel(self): return True
  def getDeltaKernel(self): return NormalDriftKernel()

  def hasVariationalLKernel(self): return True
  def getParameterScopes(self): return ["REAL","POSITIVE_REAL"]

  def gradientOfLogDensity(self,x,params):
    mu = params[0]
    sigma = params[1]

    gradMu = (x - mu) / (math.pow(sigma,2))
    gradSigma = (math.pow(x - mu,2) - math.pow(sigma,2)) / math.pow(sigma,3)
    return [gradMu,gradSigma]

class UniformOutputPSP(RandomPSP):
  # TODO don't need to be class methods
  def simulateNumeric(self,low,high): return scipy.stats.uniform.rvs(low, high-low)
  def logDensityNumeric(self,x,low,high): return scipy.stats.uniform.logpdf(x, low, high-low)

  def simulate(self,args): return self.simulateNumeric(*args.operandValues)
  def logDensity(self,x,args): return self.logDensityNumeric(x,*args.operandValues)

  # TODO Uniform presumably has a variational kernel?

class BetaOutputPSP(RandomPSP):
  # TODO don't need to be class methods
  def simulateNumeric(self,params): return scipy.stats.beta.rvs(*params)
  def logDensityNumeric(self,x,params): return scipy.stats.beta.logpdf(x,*params)

  def simulate(self,args): return self.simulateNumeric(args.operandValues)
  def logDensity(self,x,args): return self.logDensityNumeric(x,args.operandValues)

  # TODO Beta presumably has a variational kernel too?

class GammaOutputPSP(RandomPSP):
  # TODO don't need to be class methods
  def simulateNumeric(self,alpha,beta): return scipy.stats.gamma.rvs(alpha,scale=1.0/beta)
  def logDensityNumeric(self,x,alpha,beta): return scipy.stats.gamma.logpdf(x,alpha,scale=1.0/beta)

  def simulate(self,args): return self.simulateNumeric(*args.operandValues)
  def logDensity(self,x,args): return self.logDensityNumeric(x,*args.operandValues)

  # TODO Gamma presumably has a variational kernel too?

class StudentTOutputPSP(RandomPSP):
  # TODO don't need to be class methods
  def simulateNumeric(self,nu): return scipy.stats.t.rvs(nu)
  def logDensityNumeric(self,x,nu): return scipy.stats.t.logpdf(x,nu)

  def simulate(self,args): return self.simulateNumeric(*args.operandValues)
  def logDensity(self,x,args): return self.logDensityNumeric(x,*args.operandValues)

  # TODO StudentT presumably has a variational kernel too?

