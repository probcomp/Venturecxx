class Request():
  def __init__(self,esrs=[],lsrs=[]):
    self.esrs = esrs
    self.lsrs = lsrs

class ESR():
  def __init__(self,id,exp,env,block=None,subBlock=None):
    self.id = id
    self.exp = exp
    self.env = env
    self.block = block
    self.subBlock = subBlock

