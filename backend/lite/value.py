"""Venture values.

The design currently lives at
https://docs.google.com/document/d/1URnJh5hNJ___-dwzIpca5Y2h-Mku1n5zjpGCiFBcUHM/edit
"""
from abc import ABCMeta
from numbers import Number
from request import Request # TODO Pull that file in here?

# TODO Define reasonable __str__ and/or __repr__ methods for all the
# values and all the types.

class VentureValue(object):
  __metaclass__ = ABCMeta

  def getNumber(self): raise Exception("Cannot convert %s to number" % type(self))
  def getAtom(self): raise Exception("Cannot convert %s to atom" % type(self))
  def getBool(self): raise Exception("Cannot convert %s to bool" % type(self))
  def getSymbol(self): raise Exception("Cannot convert %s to symbol" % type(self))
  def getArray(self, _elt_type=None): raise Exception("Cannot convert %s to array" % type(self))
  def getPair(self): raise Exception("Cannot convert %s to pair" % type(self))
  def getSimplex(self): raise Exception("Cannot convert %s to simplex" % type(self))
  def getDict(self): raise Exception("Cannot convert %s to dict" % type(self))
  def getMatrix(self): raise Exception("Cannot convert %s to matrix" % type(self))
  def getSP(self): raise Exception("Cannot convert %s to sp" % type(self))
  def getEnvironment(self): raise Exception("Cannot convert %s to environment" % type(self))

  def asStackDict(self): raise Exception("Cannot convert %s to a stack dictionary" % type(self))
  @staticmethod
  def fromStackDict(thing):
    if isinstance(thing, list):
      # TODO Arrays or lists?
      return VentureArray([VentureValue.fromStackDict(v) for v in thing])
    else:
      return stackable_types[thing["type"]].fromStackDict(thing)

  def compare(self, other):
    st = type(self)
    ot = type(other)
    if st == ot:
      return self.compareSameType(other)
    if venture_types.index(st) < venture_types.index(ot) : return -1
    else: return 1 # We already checked for equality
  def compareSameType(self, _): raise Exception("Cannot compare %s" % type(self))
  def equal(self, other): return self.compare(other) == 0

  def lookup(self, _): raise Exception("Cannot look things up in %s" % type(self))
  def contains(self, _): raise Exception("Cannot look for things in %s" % type(self))
  def length(self): raise Exception("Cannot measure length of %s" % type(self))

  def __eq__(self, other):
    if isinstance(other, VentureValue):
      return self.equal(other)
    else:
      return False

class VentureNumber(VentureValue):
  def __init__(self,number):
    assert isinstance(number, Number)
    self.number = number
  def __repr__(self): return "Number(%s)" % self.number
  def getNumber(self): return self.number
  def asStackDict(self): return {"type":"number","value":self.number}
  @staticmethod
  def fromStackDict(thing): return VentureNumber(thing["value"])
  def compareSameType(self, other): return stupidCompare(self.number, other.number)
  def __hash__(self): return hash(self.number)

def stupidCompare(thing, other):
  # number.__cmp__(other) works for ints but not floats.  Guido, WTF!?
  # strings don't have __cmp__ either?
  if thing < other: return -1
  elif thing > other: return 1
  else: return 0

class VentureAtom(VentureValue):
  def __init__(self,atom):
    assert isinstance(atom, Number)
    self.atom = atom
  def __repr__(self): return "Atom(%s)" % self.atom
  def getNumber(self): return self.atom
  def getAtom(self): return self.atom
  def getBool(self): return self.atom
  def asStackDict(self): return {"type":"atom","value":self.atom}
  @staticmethod
  def fromStackDict(thing): return VentureAtom(thing["value"])
  def compareSameType(self, other): return stupidCompare(self.atom, other.atom)
  def __hash__(self): return hash(self.atom)

class VentureBool(VentureValue):
  def __init__(self,boolean):
    assert isinstance(boolean, bool)
    self.boolean = boolean
  def __repr__(self): return "Bool(%s)" % self.boolean
  def getBool(self): return self.boolean
  def getNumber(self):
    # TODO This horrible thing permits adding the outputs of bernoulli
    # trials as well as dispatching on them.  Or should flip and
    # bernoulli be different SPs?
    return self.boolean
  def asStackDict(self): return {"type":"boolean","value":self.boolean}
  @staticmethod
  def fromStackDict(thing): return VentureBool(thing["value"])
  def compareSameType(self, other):
    return self.boolean.__cmp__(other.boolean)
  def __hash__(self): return hash(self.boolean)

class VentureSymbol(VentureValue):
  def __init__(self,symbol): self.symbol = symbol
  def __repr__(self): return "Symbol(%s)" % self.symbol
  def getSymbol(self): return self.symbol
  def asStackDict(self): return {"type":"symbol","value":self.symbol}
  @staticmethod
  def fromStackDict(thing): return VentureSymbol(thing["value"])
  def compareSameType(self, other): return stupidCompare(self.symbol, other.symbol)
  def __hash__(self): return hash(self.symbol)

class VentureArray(VentureValue):
  """Venture arrays are heterogeneous, with O(1) access and O(n) copy.
Venture does not yet implement homogeneous packed arrays, but the
interface here is compatible with one possible path."""
  def __init__(self, array, elt_type=None):
    if elt_type is None: # No conversion
      self.array = array
    else:
      self.array = [elt_type.asVentureValue(v) for v in array]
  def getArray(self, elt_type=None):
    if elt_type is None: # No conversion
      return self.array
    else:
      return [elt_type.asPython(v) for v in self.array]
  def asPythonList(self):
    return self.array
  def asStackDict(self):
    # TODO Are venture arrays reflected as lists to the stack?
    # TODO Are stack lists lists, or are they themselves type tagged?
    return {"type":"list","value":[v.asStackDict() for v in self.array]}
  @staticmethod
  def fromStackDict(thing):
    return VentureArray([VentureValue.fromStackDict(v) for v in thing["value"]])
  def lookup(self, index):
    return self.array[int(index.getNumber())]
  def contains(self, obj):
    # Not Python's `in` because I need to use custom equality
    # TODO I am going to have to overload the equality for dicts
    # anyway, so might as well eventually use `in` here.
    return any(obj.equal(li) for li in self.array)
  def size(self): return len(self.array)

class VentureNil(VentureValue):
  def __init__(self): pass
  def __repr__(self): return "Nil"
  def compareSameType(self, _): return 0 # All Nils are equal
  def __hash__(self): return 0
  def asPythonList(self): return []
  def asStackDict(self): return {"type":"list", "value":[]}
  @staticmethod
  def fromStackDict(_): return VentureNil()
  def size(self): return 0

class VenturePair(VentureValue):
  def __init__(self,first,rest):
    assert isinstance(first, VentureValue)
    assert isinstance(rest, VentureValue)
    self.first = first
    self.rest = rest
  def getPair(self): return (self.first,self.rest)
  def asPythonList(self):
    return [self.first] + self.rest.asPythonList()
  def asStackDict(self):
    # TODO Venture pairs should be usable to build structures other
    # than proper lists.  But then, what are their types?
    return {"type":"list", "value":[v.asStackDict() for v in self.asPythonList()]}
  @staticmethod
  def fromStackDict(_): raise Exception("Type clash!")
  def compareSameType(self, other):
    fstcmp = self.first.compare(other.first)
    if fstcmp != 0: return fstcmp
    else: return self.rest.compare(other.rest)
  # TODO Define a sensible hash function
  def lookup(self, index):
    ind = index.getNumber()
    if ind < 1: # Equivalent to truncating for positive floats
      return self.first
    else:
      return self.rest.lookup(VentureNumber(ind - 1))
  def contains(self, obj): # Treat the list as a set
    if obj.equal(self.first):
      return True
    elif not isinstance(self.rest, VenturePair):
      # Notably, this means I am not checking whether the obj is the
      # last member of an improper list.
      return False
    else:
      return self.rest.contains(obj)
  def size(self): # Really, length
    return 1 + self.rest.size()

def pythonListToVentureList(*l):
  return reduce(lambda t, h: VenturePair(h, t), reversed(l), VentureNil())

class VentureSimplex(VentureValue):
  """Simplexes are homogeneous floating point arrays.  They are also
supposed to sum to 1, but we are not checking that."""
  def __init__(self,simplex): self.simplex = simplex
  def getSimplex(self): return self.simplex
  def compareSameType(self, other):
    # The Python ordering is lexicographic first, then by length, but
    # I think we want lower-d simplexes to compare less than higher-d
    # ones regardless of the point.
    lencmp = len(self.simplex).__cmp__(len(other.simplex))
    if lencmp != 0:
      return lencmp
    else:
      return self.simplex.__cmp__(other.simplex)
  def __hash__(self): return hash(self.simplex)
  def asStackDict(self):
    # TODO As what type to reflect simplex points to the stack?
    return {"type":"simplex", "value":self.simplex}
  @staticmethod
  def fromStackDict(thing): return VentureSimplex(thing["value"])
  def lookup(self, index):
    return self.simplex[index.getNumber()]
  def contains(self, obj):
    # Homogeneous; TODO make it return False instead of exploding for non-numeric objects.
    return obj.getNumber() in self.simplex
  def size(self): return len(self.simplex)

class VentureDict(VentureValue):
  def __init__(self,d): self.dict = d
  def getDict(self): return self.dict
  def asStackDict(self):
    # TODO Difficult to reflect as a Python dict because the keys
    # would presumably need to be converted to stack dicts too, which
    # is a problem because they need to be hashable.
    return {"type":"dict", "value":self}
  @staticmethod
  def fromStackDict(thing): return thing["value"]
  def lookup(self, key):
    return self.dict[key]
  def contains(self, key):
    return key in self.dict
  def size(self): return len(self.dict)

# 2D array of numbers backed by a numpy matrix object
class VentureMatrix(VentureValue):
  def __init__(self,matrix): self.matrix = matrix
  def getMatrix(self): return self.matrix
  def compareSameType(self, other):
    # TODO Are numpy matrices comparable?
    return self.matrix.__cmp__(other.matrix)
  def __hash__(self): return hash(self.matrix)
  def asStackDict(self):
    return {"type":"matrix", "value":self.matrix}
  @staticmethod
  def fromStackDict(thing): return VentureMatrix(thing["value"])

class SPRef(VentureValue):
  def __init__(self,makerNode): self.makerNode = makerNode
  def asStackDict(self): return {"type":"SP","value":self}
  @staticmethod
  def fromStackDict(thing): return thing["value"]
  # SPRefs are intentionally not comparable until we decide otherwise

## SPs and Environments as well
## Not Requests, because we do not reflect on them

venture_types = [
  VentureBool, VentureNumber, VentureAtom, VentureSymbol, VentureNil, VenturePair,
  VentureArray, VentureSimplex, VentureDict, VentureMatrix, SPRef]
  # Break load order dependency by not adding SPs and Environments yet

stackable_types = {
  "number": VentureNumber,
  "atom": VentureAtom,
  "boolean": VentureBool,
  "symbol": VentureSymbol,
  "list": VentureArray, # TODO Or should this be a linked list?  Should there be an array type?
  "simplex": VentureSimplex,
  "dict": VentureDict,
  "matrix": VentureMatrix,
  "SP": SPRef, # As opposed to VentureSP?
  }

def registerVentureType(t, name = None):
  if t in venture_types: pass
  else:
    venture_types.append(t)
    if name is not None:
      stackable_types[name] = t


class VentureType(object):
  def asPythonNoneable(self, vthing):
    if vthing is None:
      return None
    else:
      return self.asPython(vthing)

# TODO Is there any way to make these guys be proper singleton
# objects?

# This is a prototypical example of the classes I am autogenerating
# below, for legibility.  I could have removed this and added "Number"
# to the list in the for.
class NumberType(VentureType):
  def asVentureValue(self, thing): return VentureNumber(thing)
  def asPython(self, vthing): return vthing.getNumber()

for typename in ["Atom", "Bool", "Symbol", "Array", "Pair", "Simplex", "Dict", "Matrix", "SP", "Environment"]:
  # Exec is appropriate for metaprogramming, but indeed should not be used lightly.
  # pylint: disable=exec-used
  exec("""
class %sType(VentureType):
  def asVentureValue(self, thing): return Venture%s(thing)
  def asPython(self, vthing): return vthing.get%s()
""" % (typename, typename, typename))

class NilType(VentureType):
  def asVentureValue(self, _thing):
    # TODO Throw an error if not null-like?
    return VentureNil()
  def asPython(self, _vthing):
    # TODO Throw an error if not nil?
    return []

class ListType(VentureType):
  """A Venture list is either a VentureNil or a VenturePair whose
second field is a Venture list.  I choose that the corresponding
Python object is a list of VentureValue objects (this is consistent
with the Any type doing no conversion).

In Haskell type notation:

data List = Nil | Pair Any List
"""
  def asVentureValue(self, thing):
    return pythonListToVentureList(*thing)
  def asPython(self, thing):
    return thing.asPythonList()

class ExpressionType(VentureType):
  """A Venture expression is either a Venture self-evaluating object
(bool, number, atom), or a Venture symbol, or a Venture array of
Venture Expressions.  Note: I adopt the convention that, to
distinguish them from numbers, Venture Atoms will be represented in
Python as VentureAtom objects for purposes of this type.

In Haskell type notation:

data Expression = Bool | Number | Atom | Symbol | Array Expression
"""
  def asVentureValue(self, thing):
    if isinstance(thing, bool):
      return VentureBool(thing)
    if isinstance(thing, Number):
      return VentureNumber(thing)
    if isinstance(thing, VentureAtom):
      return thing
    if isinstance(thing, str):
      return VentureSymbol(thing)
    if hasattr(thing, "__getitem__"): # Already not a string
      return VentureArray([self.asVentureValue(v) for v in thing])
    else:
      raise Exception("Cannot convert Python object %r to a Venture Expression" % thing)

  def asPython(self, thing):
    if isinstance(thing, VentureBool):
      return thing.getBool()
    if isinstance(thing, VentureNumber):
      return thing.getNumber()
    if isinstance(thing, VentureAtom):
      return thing # Atoms are valid elements of expressions
    if isinstance(thing, VentureSymbol):
      return thing.getSymbol()
    if isinstance(thing, VentureArray):
      return thing.getArray(self)
    raise Exception("Cannot convert Venture object %r to a Python representation of a Venture Expression" % thing)

class AnyType(VentureType):
  """The type object to use for parametric types -- does no conversion."""
  def asVentureValue(self, thing):
    assert isinstance(thing, VentureValue)
    return thing
  def asPython(self, thing):
    assert isinstance(thing, VentureValue)
    return thing

class HomogeneousArrayType(VentureType):
  """Type objects for homogeneous arrays.  Right now, the homogeneity
  is not captured in the implementation, in that on the Venture side
  such data is still stored as heterogenous Venture arrays.  This type
  does, however, encapsulate the necessary wrapping and unwrapping."""
  def __init__(self, subtype):
    assert isinstance(subtype, VentureType)
    self.subtype = subtype
  def asVentureValue(self, thing):
    return VentureArray(thing, self.subtype)
  def asPython(self, vthing):
    return vthing.getArray(self.subtype)

class RequestType(VentureType):
  """A type object for Venture's Requests.  Requests are not Venture
  values in the strict sense, and reflection is not permitted on them.
  This type exists to permit requester PSPs to be wrapped in the
  TypedPSP wrapper."""
  def asVentureValue(self, thing):
    assert isinstance(thing, Request)
    return thing
  def asPython(self, thing):
    assert isinstance(thing, Request)
    return thing
