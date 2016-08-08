from weakref import WeakValueDictionary

import venture.lite.types as t

from venture.mite.sp import SimulationSP
from venture.mite.sp_registry import registerBuiltinSP

class InternedObject(object):
  """A class whose instances are interned, so that they can be hashed
  and compared in constant time."""

  _objects = WeakValueDictionary()

  def __new__(cls, *args):
    if (cls, args) in cls._objects:
      ret = cls._objects[(cls, args)]
    else:
      ret = super(InternedObject, cls).__new__(cls, *args)
      cls._objects[(cls, args)] = ret
    return ret

  def __copy__(self): return self
  def __deepcopy__(self, _memo): return self

class Address(InternedObject):
  """Uniquely identifies a point in a Venture program execution."""

  pass

class BuiltinAddress(Address):
  """A built-in value."""

  def __init__(self, name):
    self.name = name

class DirectiveAddress(Address):
  """A top-level directive."""

  def __init__(self, directive_id):
    self.directive_id = directive_id

class RequestAddress(Address):
  """An expression requested by a procedure."""

  def __init__(self, sp_addr, request_id):
    self.sp_addr = sp_addr
    self.request_id = request_id

class SubexpressionAddress(Address):
  """A subexpression of a combination."""

  def __init__(self, index, parent_addr):
    self.index = index
    self.parent = parent_addr

builtin = BuiltinAddress
directive = DirectiveAddress
request = RequestAddress
subexpression = SubexpressionAddress


## VentureScript bindings for constructing addresses

class AddressMakerSP(SimulationSP):
  def __init__(self, python_maker, input_types):
    self.python_maker = python_maker
    self.input_types = input_types

  def simulate(self, inputs, _prng):
    assert len(inputs) == len(self.input_types)
    inputs = [in_t.asPython(value)
              for in_t, value in zip(self.input_types, inputs)]
    return t.Blob.asVentureValue(self.python_maker(*inputs))

registerBuiltinSP("builtin", AddressMakerSP(builtin, [t.String]))
registerBuiltinSP("toplevel", AddressMakerSP(directive, [t.Int]))
registerBuiltinSP("request", AddressMakerSP(request, [t.Blob, t.Object]))
registerBuiltinSP("subexpression", AddressMakerSP(subexpression, [t.Int, t.Blob]))
