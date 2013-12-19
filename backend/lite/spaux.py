from copy import copy

class SPAux(object):
  def __init__(self, families=None):
    if families:
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
    return SPAux(copy(self.families))
