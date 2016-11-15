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

# Address construction

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

  def __init__(self, directive_id, trace_id):
    self.directive_id = directive_id
    self.trace_id = trace_id

  def __repr__(self):
    return "toplevel({!r}, {!r})".format(self.directive_id, self.trace_id)

class RequestAddress(Address):
  """An expression requested by a procedure."""

  def __init__(self, sp_addr, request_id):
    self.sp_addr = sp_addr
    self.request_id = request_id

  def __repr__(self):
    if isinstance(self.request_id, Address):
      # Assume it's probably a compound SP application.  Since those
      # may duplicate exponentially much stuff between their sp_addr
      # and their request_id, suppress some.
      return "request({!r}, {!r})".format(hash(self.sp_addr), self.request_id)
    else:
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
subexpression = SubexpressionAddress

def request(sp_addr, request_id):
  # if the request_id is a foreign blob, unpack it
  # (this happens when using the make_sp interface from Venture)
  if request_id in t.Blob:
    request_id = t.Blob.asPython(request_id)
  elif request_id in t.Pair(t.Blob, t.Object):
    request_id = t.Pair(t.Blob, t.Object).asPython(request_id)
  return RequestAddress(sp_addr, request_id)

# Address manipulations

def split_subexpression(address):
  """Split the subexpression top, if any, off an address.

  Return a pair (root, branch) where `root` is the top
  non-subexpression address occurring in the given address, and
  `branch` is the list of subexpression indexes from there."""
  if isinstance(address, SubexpressionAddress):
    (root, branch) = split_subexpression(address.parent)
    branch.append(address.index)
    return (root, branch)
  else:
    return (address, [])

def interpret_address_in_trace(address, trace_id, orig_trace_id=None):
  def recur_raw(address):
    if isinstance(address, BuiltinAddress):
      return address
    elif isinstance(address, DirectiveAddress):
      if address.trace_id is orig_trace_id:
        return directive(address.directive_id, trace_id)
      else:
        return address
    elif isinstance(address, RequestAddress):
      return RequestAddress(recur(address.sp_addr), recur(address.request_id))
    elif isinstance(address, SubexpressionAddress):
      return subexpression(address.index, recur(address.parent))
    else:
      # Cover request ids that may not be addresses.  This is wrong if
      # the request ID is a compound object that contains addresses, but
      # I hope that doesn't happen.
      return address
  table = {}
  def memoize_unary(f):
    def f_memo(x):
      if x in table:
        return table[x]
      else:
        ans = f(x)
        if x in table:
          # f mutated the table and added x
          assert ans == table[x], "Recursive invocation of memoized function produced incompatible answers"
          return table[x]
        else:
          table[x] = ans
          return ans
    return f_memo
  recur = memoize_unary(recur_raw)
  return recur(address)

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
registerBuiltinSP("toplevel", AddressMakerSP(lambda did: directive(did, None), [t.Int]))
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
