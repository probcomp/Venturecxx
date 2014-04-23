from value import VentureValue, registerVentureType, standard_venture_type

# Environments store Python strings for the symbols, not Venture
# symbol objects.  This is a choice, but whichever way it is made it
# should be consistent.
class VentureEnvironment(VentureValue):
  def __init__(self,outerEnv=None,ids=None,nodes=None):
    self.outerEnv = outerEnv
    self.frame = {}
    if ids:
      for sym in ids:
        assert isinstance(sym, str)
    if ids and nodes: self.frame.update(zip(ids,nodes))

  def addBinding(self,sym,val):
    assert isinstance(sym, str)
    assert not sym in self.frame
    self.frame[sym] = val

  def findSymbol(self,sym):
    if sym in self.frame: return self.frame[sym]
    elif not self.outerEnv: raise Exception("Cannot find symbol %s" % sym)
    else: return self.outerEnv.findSymbol(sym)
  # VentureEnvironments are intentionally not comparable until we
  # decide otherwise

  def getEnvironment(self): return self

  def asStackDict(self, _trace):
    # Methinks environments can be pretty opaque things for now.
    return {"type":"environment", "value":self}
  @staticmethod
  def fromStackDict(thing): return thing["value"]

  def lookup(self, key):
    return self.findSymbol(key.getSymbol())
  # TODO Define contains to check whether the symbol is there (without throwing exceptions)

registerVentureType(VentureEnvironment, "environment")
# Exec is appropriate for metaprogramming
from value import VentureType # Used by the exec pylint: disable=unused-import
exec(standard_venture_type("Environment")) # pylint: disable=exec-used
