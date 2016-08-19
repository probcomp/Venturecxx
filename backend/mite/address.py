from weakref import WeakValueDictionary

import venture.lite.types as t
from venture.lite.value import VentureValue

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

  def __repr__(self):
    return "builtin({!r})".format(self.name)

class DirectiveAddress(Address):
  """A top-level directive."""

  def __init__(self, directive_id):
    self.directive_id = directive_id

  def __repr__(self):
    return "toplevel({!r})".format(self.directive_id)

class RequestAddress(Address):
  """An expression requested by a procedure."""

  def __new__(cls, sp_addr, request_id):
    # if the request_id is a foreign blob, unpack it
    # (this happens when using the make_sp interface from Venture)
    if request_id in t.Blob:
      request_id = t.Blob.asPython(request_id)
    elif request_id in t.Pair(t.Blob, t.Object):
      request_id = t.Pair(t.Blob, t.Object).asPython(request_id)
    return super(RequestAddress, cls).__new__(cls, sp_addr, request_id)

  def __init__(self, sp_addr, request_id):
    self.sp_addr = sp_addr
    self.request_id = request_id

  def __repr__(self):
    return "request({!r}, {!r})".format(self.sp_addr, self.request_id)

class SubexpressionAddress(Address):
  """A subexpression of a combination."""

  def __init__(self, index, parent_addr):
    self.index = index
    self.parent = parent_addr

  def __repr__(self):
    return "subexpression({!r}, {!r})".format(self.index, self.parent)

builtin = BuiltinAddress
directive = DirectiveAddress
toplevel = DirectiveAddress
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
registerBuiltinSP("toplevel", AddressMakerSP(toplevel, [t.Int]))
registerBuiltinSP("request", AddressMakerSP(request, [t.Blob, t.Object]))
registerBuiltinSP("subexpression", AddressMakerSP(subexpression, [t.Int, t.Blob]))


## HACK for allowing SPs to get the addresses of their inputs:
## values which carry hidden address metadata with them

class VentureAddressed(VentureValue):
  def __init__(self, address, value):
    self.address = address
    self.value = value

  def getNumber(self): return self.value.getNumber()
  def getInteger(self): return self.value.getInteger()
  def getAtom(self): return self.value.getAtom()
  def getBool(self): return self.value.getBool()
  def getSymbol(self): return self.value.getSymbol()
  def getString(self): return self.value.getString()
  def getForeignBlob(self): return self.value.getForeignBlob()
  def getPair(self): return self.value.getPair()
  def getArray(self, elt_type): return self.value.getArray(elt_type)
  def getSimplex(self): return self.value.getSimplex()
  def getDict(self): return self.value.getDict()
  def getMatrix(self): return self.value.getMatrix()
  def getSymmetricMatrix(self): return self.value.getSymmetricMatrix()
  def getSP(self): return self.value.getSP()
  def getEnvironment(self): return self.value.getEnvironment()

  def asStackDict(self, trace=None):
    return dict(self.value.asStackDict(trace), address=self.address)

  @staticmethod
  def fromStackDict(thing):
    return VentureAddressed(
      thing["address"], VentureValue.fromStackDict(thing))

  # TODO fill in the rest of the methods

class AddressOfSP(SimulationSP):
  def simulate(self, inputs, _prng):
    assert len(inputs) == 1
    [x] = inputs
    assert isinstance(x, VentureAddressed)
    return t.Blob.asVentureValue(x.address)

class ValueOfSP(SimulationSP):
  def simulate(self, inputs, _prng):
    assert len(inputs) == 1
    [x] = inputs
    assert isinstance(x, VentureAddressed)
    return x.value

registerBuiltinSP("address_of", AddressOfSP())
registerBuiltinSP("value_of", ValueOfSP())
