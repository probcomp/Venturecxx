import scipy.stats

from psp import PSP

class NormalOutputPSP(PSP):
  # TODO don't need to be class methods
  def normalSample(self,mu,sigma): return scipy.stats.norm.rvs(mu,sigma)
  def normalLogDensity(self,x,mu,sigma): return scipy.stats.norm.logpdf(x,mu,sigma)
    
  def simulate(self,args):
    (mu,sigma) = args.operandValues[0:2]
    return self.normalSample(mu,sigma)

  def logDensity(self,x,args):
    (mu,sigma) = args.operandValues[0:2]
    return self.normalLogDensity(x,mu,sigma)

  def canAbsorb(self): return True
      
