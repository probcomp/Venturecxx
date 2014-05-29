from value import VentureValue, registerVentureType, standard_venture_type
import serialize

# Environments store Python strings for the symbols, not Venture
# symbol objects.  This is a choice, but whichever way it is made it
# should be consistent.
@serialize.register
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

  def removeBinding(self,sym):
    assert isinstance(sym, str)
    if sym in self.frame: del self.frame[sym]
    elif not self.outerEnv: raise Exception("Cannot unbind unbound symbol %s" % sym)
    else: self.outerEnv.removeBinding(sym)

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

  def equalSameType(self, other):
    # This compares node identities, not their contents.  This is as
    # it should be, because nodes can mutate.
    if self.frame == other.frame:
      return (self.outerEnv is None and other.outerEnv is None) or \
        self.outerEnv.equalSameType(other.outerEnv)
    else: return False

  def lookup(self, key):
    return self.findSymbol(key.getSymbol())
  # TODO Define contains to check whether the symbol is there (without throwing exceptions)

  # for serialization
  cyclic = True

registerVentureType(VentureEnvironment, "environment")
# Exec is appropriate for metaprogramming
from value import VentureType # Used by the exec pylint: disable=unused-import
exec(standard_venture_type("Environment")) # pylint: disable=exec-used
