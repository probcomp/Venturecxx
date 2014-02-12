from abc import ABCMeta
from numbers import Number

class VentureValue(object):
  __metaclass__ = ABCMeta

  def getNumber(self): raise Exception("Cannot convert %s to number" % type(self))
  def getAtom(self): raise Exception("Cannot convert %s to atom" % type(self))
  def getBool(self): raise Exception("Cannot convert %s to bool" % type(self))
  def getSymbol(self): raise Exception("Cannot convert %s to symbol" % type(self))
  def getArray(self, elt_type=None): raise Exception("Cannot convert %s to array" % type(self))
  def getPair(self): raise Exception("Cannot convert %s to pair" % type(self))
  def getSimplex(self): raise Exception("Cannot convert %s to simplex" % type(self))
  def getDict(self): raise Exception("Cannot convert %s to dict" % type(self))
  def getMatrix(self): raise Exception("Cannot convert %s to matrix" % type(self))
  def getSP(self): raise Exception("Cannot convert %s to sp" % type(self))
  def getEnvironment(self): raise Exception("Cannot convert %s to environment" % type(self))

  def asStackDict(self): raise Exception("Cannot convert %s to a stack dictionary" % type(self))

  def compare(self, other):
    st = type(self)
    ot = type(other)
    if st == ot:
      return self.compareSameType(other)
    if venture_types.index(st) < venture_types.index(ot) : return -1
    else: return 1 # We already checked for equality

  def compareSameType(self, _): raise Exception("Cannot compare %s" % type(self))

class VentureNumber(VentureValue):
  def __init__(self,number): self.number = number
  def getNumber(self): return self.number
  def asStackDict(self): return {"type":"number","value":self.number}
  def compareSameType(self, other):
    return self.number.__cmp__(other.number)

class VentureAtom(VentureValue):
  def __init__(self,atom): self.atom = atom
  def getNumber(self): return self.atom
  def getAtom(self): return self.atom
  def getBool(self): return self.atom
  def asStackDict(self): return {"type":"atom","value":self.atom}
  def compareSameType(self, other):
    return self.atom.__cmp__(other.atom)

class VentureBool(VentureValue):
  def __init__(self,boolean): self.boolean = boolean
  def getBool(self): return self.boolean
  def asStackDict(self): return {"type":"boolean","value":self.boolean}
  def compareSameType(self, other):
    return self.boolean.__cmp__(other.boolean)

class VentureSymbol(VentureValue):
  def __init__(self,symbol): self.symbol = symbol
  def getSymbol(self): return self.symbol
  def asStackDict(self): return {"type":"symbol","value":self.symbol}
  def compareSameType(self, other):
    return self.symbol.__cmp__(other.symbol)

# Venture arrays are heterogeneous, with O(1) access and O(n) copy.
# Venture does not yet have a story for homogeneous packed arrays.
class VentureArray(VentureValue):
  def __init__(self,array): self.array = array
  def getArray(self, elt_type=None):
    if elt_type is None: # No conversion
      return self.array
    else:
      return [elt_type.asPython(v) for v in self.array]
  def asStackDict(self):
    # TODO Are venture arrays reflected as lists to the stack?
    return {"type":"list","value":[v.asStackDict() for v in self.array]}

class VentureNil(VentureValue):
  def __init__(self): pass
  def compareSameType(self, _): return 0 # All Nils are equal

class VenturePair(VentureValue):
  def __init__(self,first,rest):
    assert isinstance(first, VentureValue)
    assert isinstance(rest, VentureValue)
    self.first = first
    self.rest = rest
  def getPair(self): return (self.first,self.rest)
  def compareSameType(self, other):
    fstcmp = self.first.compare(other.first)
    if fstcmp != 0: return fstcmp
    else: return self.rest.compare(other.rest)

# Simplexes are homogeneous floating point arrays.  They are also
# supposed to sum to 1, but we are not checking that.
class VentureSimplex(VentureValue):
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

class VentureDict(VentureValue):
  def __init__(self,d): self.dict = d
  def getDict(self): return self.dict

# Backed by a numpy matrix object
class VentureMatrix(VentureValue):
  def __init__(self,matrix): self.matrix = matrix
  def getMatrix(self): return self.matrix
  def compareSameType(self, other):
    # TODO Are numpy matrices comparable?
    return self.matrix.__cmp__(other.matrix)

class SPRef(VentureValue):
  def __init__(self,makerNode): self.makerNode = makerNode
  def asStackDict(self): return {"type":"SP","value":self}
  # SPRefs are intentionally not comparable until we decide otherwise

## SPs and Environments as well
## Not Requests, because we do not reflect on them

venture_types = [VentureBool, VentureNumber, VentureAtom, VentureSymbol, VentureNil, VenturePair, VentureArray, VentureSimplex, VentureDict, VentureMatrix, SPRef] # Break load order dependency but not adding SPs and Environments yet

def registerVentureType(t):
  if t in venture_types: pass
  else: venture_types.append(t)

def isVentureValue(thing):
  return thing is None or isinstance(thing, VentureValue)

class VentureType(object): pass

# TODO Is there any way to make these guys be proper singleton
# objects?

# This is a prototypical example of the classes I am autogenerating
# below, for legibility.  I could have removed this and added "Number"
# to the list in the for.
class NumberType(VentureType):
  def asVentureValue(self, thing): return VentureNumber(thing)
  def asPython(self, vthing): return vthing.getNumber()

# TODO Also Nil?
for typename in ["Atom", "Bool", "Symbol", "Array", "Pair", "Simplex", "Dict", "Matrix", "SP", "Environment"]:
  # Exec is appropriate for metaprogramming, but indeed should not be used lightly.
  # pylint: disable=exec-used
  exec("""
class %sType(VentureType):
  def asVentureValue(self, thing): return Venture%s(thing)
  def asPython(self, vthing): return vthing.get%s()
""" % (typename, typename, typename))

class NilType(VentureType):
  def asVentureValue(self, thing):
    # TODO Throw an error if not null-like?
    return VentureNil()
  def asPython(self, vthing):
    # TODO Throw an error if not nil?
    return []

# A Venture expression is either a Venture self-evaluating object
# (bool, number, atom), or a Venture symbol, or a Venture array of
# Venture Expressions.
# data Expression = Bool | Number | Atom | Symbol | Array Expression
class ExpressionType(VentureType):
  def asVentureValue(self, thing):
    if isinstance(thing, bool):
      return VentureBool(thing)
    if isinstance(thing, Number):
      return VentureNumber(thing)
    # TODO How do we actually evaluate literal atoms?
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
      return thing.getAtom()
    if isinstance(thing, VentureSymbol):
      return thing.getSymbol()
    if isinstance(thing, VentureArray):
      return thing.getArray(self)

# Parametric values -- no conversion
class AnyType(VentureType):
  def asVentureValue(self, thing):
    assert isinstance(thing, VentureValue)
    return thing
  def asPython(self, thing):
    assert isinstance(thing, VentureValue)
    return thing
