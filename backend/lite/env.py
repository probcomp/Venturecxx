# Copyright (c) 2013, 2014 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

from value import VentureValue, registerVentureType
from exception import VentureError

# Environments store Python strings for the symbols, not Venture
# symbol objects.  This is a choice, but whichever way it is made it
# should be consistent.
# Binding a symbol to the Python value None has the effect of making
# the symbol behave as if unbound, shadowing existing bindings; this
# behavior is used in the implementation of letrec.
class VentureEnvironment(VentureValue):
  def __init__(self,outerEnv=None,ids=None,nodes=None):
    self.outerEnv = outerEnv
    self.frame = {}
    if ids:
      for sym in ids:
        assert isinstance(sym, str)
    if ids and nodes: self.frame.update(zip(ids,nodes))

  def addBinding(self,sym,val):
    if not isinstance(sym, str):
      raise VentureError("Symbol '%s' must be a string, not %s" % (str(sym), type(sym)))
    if sym in self.frame:
      raise VentureError("Symbol '%s' already bound" % sym)
    self.frame[sym] = val

  def removeBinding(self,sym):
    assert isinstance(sym, str)
    if sym in self.frame: del self.frame[sym]
    elif not self.outerEnv: raise VentureError("Cannot unbind unbound symbol '%s'" % sym)
    else: self.outerEnv.removeBinding(sym)

  def replaceBinding(self,sym,val):
    # Used in the implementation of letrec
    assert isinstance(sym, str)
    assert sym in self.frame
    assert self.frame[sym] is None
    self.frame[sym] = val

  def findSymbol(self,sym):
    if sym in self.frame: ret = self.frame[sym]
    elif not self.outerEnv: ret = None
    else: ret = self.outerEnv.findSymbol(sym)
    if ret is None:
      raise VentureError("Cannot find symbol '%s'" % sym)
    return ret

  def symbolBound(self, sym):
    if sym in self.frame: return self.frame[sym] is not None
    elif not self.outerEnv: return False
    else: return self.outerEnv.symbolBound(sym)

  # VentureEnvironments are intentionally not comparable until we
  # decide otherwise

  def getEnvironment(self): return self

  def asStackDict(self, _trace=None):
    # Methinks environments can be pretty opaque things for now.
    return {"type":"environment", "value":self}
  @staticmethod
  def fromStackDict(thing): return thing["value"]

  def equalSameType(self, other):
    # This compares node identities, not their contents.  This is as
    # it should be, because nodes can mutate.
    if self.frame == other.frame:
      if self.outerEnv is None:
        return other.outerEnv is None
      elif other.outerEnv is None:
        return False
      else:
        return self.outerEnv.equalSameType(other.outerEnv)
    else: return False

  def lookup(self, key):
    return self.findSymbol(key.getSymbol())
  # TODO Define contains to check whether the symbol is there (without throwing exceptions)

registerVentureType(VentureEnvironment, "environment")
# Exec is appropriate for metaprogramming
from types import VentureType, standard_venture_type # Used by the exec pylint: disable=unused-import
exec(standard_venture_type("Environment")) # pylint: disable=exec-used
