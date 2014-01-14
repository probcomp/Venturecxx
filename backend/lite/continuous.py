import scipy.stats
import math

from psp import PSP,RandomPSP

class NormalOutputPSP(RandomPSP):
  # TODO don't need to be class methods
  def simulateNumeric(self,params): return scipy.stats.norm.rvs(*params)
  def logDensityNumeric(self,x,params): return scipy.stats.norm.logpdf(x,*params)

  def simulate(self,args): return self.simulateNumeric(args.operandValues)
  def logDensity(self,x,args): return self.logDensityNumeric(x,args.operandValues)

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
