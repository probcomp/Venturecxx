class OmegaDB():
  def __init__(self):
    self.latentDBs = {} # not sure if keys are nodes or sps
    self.drgDB = {}
    self.spFamilyDBs = {} # makerNode,id => root
