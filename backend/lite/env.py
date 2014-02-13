from value import VentureValue, registerVentureType

class VentureEnvironment(VentureValue):
  def __init__(self,outerEnv=None,ids=None,nodes=None):
    self.outerEnv = outerEnv
    self.frame = {}
    if ids and nodes: self.frame.update(zip(ids,nodes))

  def addBinding(self,sym,val):
    assert not sym in self.frame
    self.frame[sym] = val

  def findSymbol(self,sym):
    if sym in self.frame: return self.frame[sym]
    elif not self.outerEnv: raise Exception("Cannot find symbol %s" % sym)
    else: return self.outerEnv.findSymbol(sym)
  # VentureEnvironments are intentionally not comparable until we
  # decide otherwise

  def asStackDict(self):
    # Methinks environments can be pretty opaque things for now.
    return {"type":"environment", "value":self}

  def lookup(self, key):
    return self.findSymbol(key.asSymbol())
  # TODO Define contains to check whether the symbol is there (without throwing exceptions)

registerVentureType(VentureEnvironment)
