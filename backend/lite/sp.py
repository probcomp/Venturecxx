from abc import ABCMeta, abstractmethod

class SP():
  __metaclass__ = ABCMeta

  def __init__(self,requestPSP,outputPSP):
    self.requestPSP = requestPSP
    self.outputPSP = outputPSP

  def constructSPAux(self): return None
  def constructLatentDB(self): return None
  def simulateLatents(self,spaux,lsr,shouldRestore,latentDB): pass
  def detachLatents(self,spaux,lsr,latentDB): pass
  def hasAEKernel(self): return False
