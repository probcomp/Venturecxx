import scipy.stats
import scipy.special
import math
import random
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


class GammaOutputPSP(RandomPSP):
  def simulate(self,args):
    (alpha,beta) = args.operandValues
    return random.gammavariate(alpha,beta)

  def logDensity(self,x,args):
    (alpha,beta) = args.operandValues
    term1 = (alpha - 1) * math.log(x) - x/beta
    term2 = scipy.special.gammaln(alpha) + alpha * math.log(beta)
    return term1 - term2
