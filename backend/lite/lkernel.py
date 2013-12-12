from abc import ABCMeta, abstractmethod
from sp import SP

class LKernel():
  __metaclass__ = ABCMeta

  @abstractmethod
  def simulate(self,oldValue,args): pass

  def weight(self,newValue,oldValue,args): return 0

  def reverseWeight(self,oldValue,args):
    return self.weight(oldValue,None,args)

class DefaultAAALKernel(LKernel):
  def __init__(self,makerPSP): self.makerPSP = makerPSP

  def simulate(self,oldValue,args): return self.makerPSP.simulate(args)
    
  def weight(self,newValue,oldValue,args):
    assert isinstance(newValue,SP)
    return newValue.logDensityOfCounts(args.madeSPAux)

class DeterministicLKernel(LKernel):
  def __init__(self,value,sp): 
    self.value = value
    self.sp = sp

  def simulate(self,oldValue,args): return self.value
  def weight(self,newValue,oldValue,args): return self.sp.logDensity(newValue,args)
