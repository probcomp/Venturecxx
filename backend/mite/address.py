from weakref import WeakValueDictionary

from venture.lite.address import List

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
