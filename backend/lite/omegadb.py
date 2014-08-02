class OmegaDB(object):
  def __init__(self):
    self.latentDBs = {} # not sure if keys are nodes or sps
    self.values = {} # node => value
    self.spFamilyDBs = {} # makerNode,id => root

    # The partial derivative of the weight returned by the detach that
    # made this DB with respect to the value of this node, at the
    # value stored for this node in self.values.  Only meaningful for
    # nodes with continuous values.
    self.partials = {} # node => cotangent(value)

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

  def hasESRParent(self,sp,id): return (sp,id) in self.spFamilyDBs
  def getESRParent(self,sp,id): return self.spFamilyDBs[(sp,id)]
  def registerSPFamily(self,sp,id,esrParent):
    assert not (sp,id) in self.spFamilyDBs
    self.spFamilyDBs[(sp,id)] = esrParent

  def addPartials(self, nodes, partials):
    assert len(nodes) == len(partials)
    for (n, p) in zip(nodes, partials):
      self.addPartial(n, p)

  def addPartial(self, node, partial):
    if node not in self.partials:
      # TODO Get the correct zero for structured partials for
      # e.g. nodes with multi-dimensional outputs.
      self.partials[node] = 0
    self.partials[node] += partial

  def getPartial(self, node):
    if node not in self.partials:
      self.partials[node] = 0
    return self.partials[node]
