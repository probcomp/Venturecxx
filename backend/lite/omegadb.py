class OmegaDB():
  def __init__(self):
    self.latentDBs = {} # not sure if keys are nodes or sps
    self.values = {} # node => value
    self.spFamilyDBs = {} # makerNode,id => root

  def hasValueFor(self,node): return node in self.values
  def getValue(self,node): return self.values[node]

  def extractValue(self,node,value):
    assert not node in self.values
    self.values[node] = value

  def hasLatentDB(self,sp): return sp in self.latentDBs

  def registerLatentDB(self,sp,latentDB):
    assert not sp in self.latentDBs
    self.latentDBs[sp] = latentDB

  def getLatentDB(self,sp): return self.latentDBs[sp]

  def getESRParent(self,sp,id): return self.spFamilyDBs[(sp,id)]
  def registerSPFamily(self,sp,id,esrParent):
    assert not (sp,id) in self.spFamilyDBs
    self.spFamilyDBs[(sp,id)] = esrParent

