class Env():
  def __init__(self):
    self.outerEnv = None
    self.frame = {}

  def __init__(self,outerEnv):
    self.outerEnv = outerEnv
    self.frame = {}

  def __init__(self,outerEnv,ids,nodes):
    self.outerEnv = outerEnv
    self.frame = {}
    self.update(zip(ids,nodes))

  def addBinding(self,sym,val):
    assert not sym in self.frame
    self.frame[sym] = val

  def findSymbol(self,sym):
    if sym in self.frame: return self.frame[sym]
    elif not self.outerEnv: raise Exception("Cannot find symbol %s" % sym)
    else: return self.outerEnv.findSymbol(sym)
