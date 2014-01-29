from abc import ABCMeta, abstractmethod

class SPFamilies(object):
  def __init__(self, families=None):
    if families:
      assert type(families) is dict
      self.families = families
    else:
      self.families = {} # id => node

  def containsFamily(self,id): return id in self.families
  def getFamily(self,id): return self.families[id]
  def registerFamily(self,id,esrParent): 
    assert not id in self.families
    self.families[id] = esrParent
  def unregisterFamily(self,id): del self.families[id]

  def copy(self):
    return SPFamilies(self.families.copy())
  
class SPAux(object):
  def copy(self): return SPAux()

class SP(object):
  __metaclass__ = ABCMeta

  def __init__(self,requestPSP,outputPSP):
    self.requestPSP = requestPSP
    self.outputPSP = outputPSP

  def constructSPAux(self): return SPAux()
  def constructLatentDB(self): return None
  def simulateLatents(self,spaux,lsr,shouldRestore,latentDB): pass
  def detachLatents(self,spaux,lsr,latentDB): pass
  def hasAEKernel(self): return False
  def description(self,name):
    candidate = self.outputPSP.description(name)
    if candidate:
      return candidate
    candidate = self.requestPSP.description(name)
    if candidate:
      return candidate
    return name
