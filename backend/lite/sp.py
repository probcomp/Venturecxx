# Copyright (c) 2013, 2014, 2015 MIT Probabilistic Computing Project.
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

from value import VentureValue, registerVentureType, VentureNil
from types import VentureType
from exception import VentureError
import venture.value.dicts as v

class SPFamilies(object):
  def __init__(self, families=None):
    if families:
      assert type(families) is dict
      self.families = families
    else:
      self.families = {} # id => node

  def containsFamily(self,id): return id in self.families
  def getFamily(self,id): return self.families[id]
  def registerFamily(self,id,esrParent):
    assert not id in self.families
    self.families[id] = esrParent
  def unregisterFamily(self,id): del self.families[id]

  def copy(self):
    return SPFamilies(self.families.copy())

class SPAux(object):
  def copy(self): return SPAux()
  def asVentureValue(self): return VentureNil()
  @staticmethod
  def fromVentureValue(_thing):
    raise Exception("Cannot convert a Venture value into a generic SPAux")

class SP(object):
  def __init__(self,requestPSP,outputPSP):
    from psp import PSP
    self.requestPSP = requestPSP
    self.outputPSP = outputPSP
    assert isinstance(requestPSP, PSP)
    assert isinstance(outputPSP, PSP)

  def constructSPAux(self): return SPAux()
  def constructLatentDB(self): return None
  def simulateLatents(self,spaux,lsr,shouldRestore,latentDB): pass
  def detachLatents(self,spaux,lsr,latentDB): pass
  def hasAEKernel(self): return False
  def show(self, _spaux): return "<procedure>"
  def description(self,name):
    candidate = self.outputPSP.description(name)
    if candidate:
      return candidate
    candidate = self.requestPSP.description(name)
    if candidate:
      return candidate
    return name
  def description_rst_format(self,name):
    candidate = self.outputPSP.description_rst_format(name)
    if candidate:
      return candidate
    candidate = self.requestPSP.description_rst_format(name)
    if candidate:
      return candidate
    return (".. function:: %s" % name, name)
  def venture_type(self):
    if hasattr(self.outputPSP, "f_type"):
      return self.outputPSP.f_type
    else:
      return self.requestPSP.f_type
  # VentureSPs are intentionally not comparable until we decide
  # otherwise

class VentureSPRecord(VentureValue):
  def __init__(self, sp, spAux=None, spFamilies=None):
    if spAux is None:
      spAux = sp.constructSPAux()
    if spFamilies is None:
      spFamilies = SPFamilies()
    self.sp = sp
    self.spAux = spAux
    self.spFamilies = spFamilies

  def show(self):
    return self.sp.show(self.spAux)

  def asStackDict(self, _trace=None):
    return v.sp(self.show(), self.spAux.asVentureValue().asStackDict())

registerVentureType(VentureSPRecord)

class UnwrappingArgs(object):
  def __init__(self, f_type, args):
    self.f_type = f_type
    self.args = args
    self.node = args.node
    self.operandNodes = args.operandNodes
    self.env = args.env

  def operandValues(self):
    return self.f_type.unwrap_arg_list(self.args.operandValues())
  def spaux(self): return self.args.spaux()

  # These four are only used on output nodes
  def requestValue(self): return self.args.requestValue()
  def esrNodes(self): return self.args.esrNodes()
  def esrValues(self): return self.args.esrValues()
  def madeSPAux(self): return self.args.madeSPAux()

  def __repr__(self):
    return "%s(%r)" % (self.__class__, self.__dict__)

class SPType(VentureType):
  """An object representing a Venture function type.  It knows
the types expected for the arguments and the return, and thus knows
how to wrap and unwrap individual values or Args objects.  This is
used in the implementation of TypedPSP and TypedLKernel."""
  def asVentureValue(self, thing): return thing
  def asPython(self, vthing): return vthing
  def distribution(self, _base, **_kwargs):
    return None
  def __contains__(self, vthing): return isinstance(vthing, VentureSPRecord)

  def __init__(self, args_types, return_type, variadic=False, min_req_args=None):
    """args_types is expected to be a Python list of instances of venture.lite.sp.VentureType,
    and return_type is expected to be one instance of same.

    See also the "Types" section of doc/type-system.md."""
    self.args_types = args_types
    self.return_type = return_type
    self.variadic = variadic
    self.min_req_args = len(args_types) if min_req_args is None else min_req_args

  def wrap_return(self, value):
    try:
      return self.return_type.asVentureValue(value)
    except VentureError as e:
      e.message = "Wrong return type: " + e.message
      raise e
  def unwrap_return(self, value):
    # value could be None for e.g. a "delta kernel" that is expected,
    # by e.g. pgibbs, to actually be a simulation kernel; also when
    # computing log density bounds over a torus for rejection
    # sampling.
    return self.return_type.asPythonNoneable(value)
  def unwrap_args(self, args):
    return UnwrappingArgs(self, args)

  def args_match(self, args):
    vals = args.operandValues()
    if not self.variadic:
      if len(vals) < self.min_req_args or len(vals) > len(self.args_types):
        return False
      return all((val in self.args_types[i] for (i,val) in enumerate(vals)))
    else:
      min_req_args = len(self.args_types) - 1
      if len(vals) < min_req_args: return False
      first_args = all((val in self.args_types[i] for (i,val) in enumerate(vals[:min_req_args])))
      rest_args = all((val in self.args_types[-1] for (i,val) in enumerate(vals[min_req_args:])))
      return first_args and rest_args

  def unwrap_arg_list(self, lst):
    if not self.variadic:
      if len(lst) < self.min_req_args:
        raise VentureError("Too few arguments: SP requires at least %d args, got only %d." % (self.min_req_args, len(lst)))
      if len(lst) > len(self.args_types):
        raise VentureError("Too many arguments: SP takes at most %d args, got %d." % (len(self.args_types), len(lst)))
      # v could be None when computing log density bounds for a torus
      return [self.args_types[i].asPythonNoneable(val) for (i,val) in enumerate(lst)]
    else:
      min_req_args = len(self.args_types) - 1
      if len(lst) < min_req_args:
        raise VentureError("Too few arguments: SP requires at least %d args, got only %d." % (min_req_args, len(lst)))
      first_args = [self.args_types[i].asPythonNoneable(val) for (i,val) in enumerate(lst[:min_req_args])]
      rest_args = [self.args_types[-1].asPythonNoneable(val) for val in lst[min_req_args:]]
      return first_args + rest_args

  def wrap_arg_list(self, lst):
    if not self.variadic:
      assert len(lst) >= self.min_req_args
      assert len(lst) <= len(self.args_types)
      # v could be None when computing log density bounds for a torus
      return [self.args_types[i].asVentureValue(val) for (i,val) in enumerate(lst)]
    else:
      min_req_args = len(self.args_types) - 1
      assert len(lst) >= min_req_args
      first_args = [self.args_types[i].asVentureValue(val) for (i,val) in enumerate(lst[:min_req_args])]
      rest_args = [self.args_types[-1].asVentureValue(val) for val in lst[min_req_args:]]
      return first_args + rest_args

  def _name_for_fixed_arity(self, args_types):
    args_spec = " ".join([t.name() for t in args_types])
    variadicity_mark = " ..." if self.variadic else ""
    return_spec = self.return_type.name()
    return "<SP %s%s -> %s>" % (args_spec, variadicity_mark, return_spec)

  def names(self):
    """One name for each possible arity of this procedure."""
    return [self._name_for_fixed_arity(self.args_types[0:i]) for i in range(self.min_req_args, len(self.args_types) + 1)]

  def name(self):
    """A default name for when there is only room for one name."""
    return self._name_for_fixed_arity(self.args_types)

  def name_rst_format(self, name):
    def subtype_name(tp):
      if hasattr(tp, "name_rst_format"):
        return tp.name_rst_format("proc")
      else:
        return tp.name()
    result = name + "("
    for (i, arg) in enumerate(self.args_types):
      if i >= self.min_req_args:
        result += "["
      if i > 0:
        result += ", "
      result += subtype_name(arg)
    if self.variadic: result += ", ..."
    result += "]" * (len(self.args_types) - self.min_req_args)
    result += ")"
    if name != "proc":
      # Top-level
      result += "\n\n   :rtype: " + subtype_name(self.return_type)
    else:
      result += " -> " + subtype_name(self.return_type)
    return result

  def gradient_type(self):
    return SPType([t.gradient_type() for t in self.args_types], self.return_type.gradient_type(), self.variadic, self.min_req_args)
