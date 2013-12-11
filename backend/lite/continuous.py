import scipy.stats

from psp import PSP

class NormalOutputPSP(PSP):
  def normalSample(mu,sigma): return scipy.stats.norm.rvs(mu,sigma)
  def normalLogDensity(x,mu,sigma): return scipy.stats.norm.logpdf(x,mu,sigma)
    
  def simulate(self,args):
    (mu,sigma) = args.operandValues[0:2]
    return normalSample(mu,sigma)

  def logDensity(self,x,args):
    (mu,sigma) = args.operandValues[0:2]
    return normalLogDensity(x,mu,sigma)

  def canAbsorb(self): return True
      
