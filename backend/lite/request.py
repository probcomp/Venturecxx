class Request(object):
  def __init__(self,esrs=None,lsrs=None):
    if esrs is None: esrs = []
    if lsrs is None: lsrs = []
    self.esrs = esrs
    self.lsrs = lsrs

class ESR(object):
  def __init__(self,id,exp,env,block=None,subBlock=None):
    self.id = id
    self.exp = exp
    self.env = env
    self.block = block
    self.subBlock = subBlock

