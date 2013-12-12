import scipy.stats

from psp import PSP,RandomPSP

class NormalOutputPSP(RandomPSP):
  # TODO don't need to be class methods
  def normalSample(self,mu,sigma): return scipy.stats.norm.rvs(mu,sigma)
  def normalLogDensity(self,x,mu,sigma): return scipy.stats.norm.logpdf(x,mu,sigma)
    
  def simulate(self,args):
    (mu,sigma) = args.operandValues[0:2]
    return self.normalSample(mu,sigma)

  def logDensity(self,x,args):
    (mu,sigma) = args.operandValues[0:2]
    ld = self.normalLogDensity(x,mu,sigma)
#    print "normal.ld(%d,%d,%d) = %d" % (x,mu,sigma,ld)
    return ld
