from abc import ABCMeta, abstractmethod

class LKernel(object):
  __metaclass__ = ABCMeta

  @abstractmethod
  def simulate(self,oldValue,args,latentDB): pass

  def weight(self,newValue,oldValue,args,latentDB): return 0

  def reverseWeight(self,oldValue,args,latentDB): 
    return self.weight(oldValue,None,args,latentDB)

class DefaultAAALKernel(LKernel):
  def __init__(self,makerPSP): self.makerPSP = makerPSP

  def simulate(self,oldValue,args,latentDB): return self.makerPSP.simulate(args)
    
  def weight(self,newValue,oldValue,args,latentDB):
    assert isinstance(newValue,SP)
    return newValue.logDensityOfCounts(args.madeSPAux)

class DeterministicLKernel(LKernel):
  def __init__(self,value,sp): 
    self.value = value
    self.sp = sp

  def simulate(self,oldValue,args,latentDB): return self.value
  def weight(self,newValue,oldValue,args,latentDB): return self.sp.logDensity(newValue,args)
