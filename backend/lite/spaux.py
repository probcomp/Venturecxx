class SPAux():
  def __init__(self): self.families = {} # id => node
  def containsFamily(self,id): return id in self.families
  def getFamily(self,id): return self.families[id]
  def registerFamily(self,id,esrParent): 
    assert not id in self.families
    self.families[id] = esrParent
