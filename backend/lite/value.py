# Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
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

"""Venture values.

The design currently lives in doc/type-system.md
"""
import operator
from numbers import Number
import numpy as np
import hashlib

from mlens import MLens
import ensure_numpy as enp
from exception import VentureValueError, VentureTypeError
import venture.value.dicts as v

# TODO Define reasonable __str__ and/or __repr__ methods for all the
# values and all the types.

class VentureValue(object):
  """Base class of all Venture values."""
  ### "natural" representation and conversions
  def getNumber(self): raise VentureTypeError("Cannot convert %s to number" % type(self))
  def getInteger(self): raise VentureTypeError("Cannot convert %s to integer" % type(self))
  def getProbability(self): raise VentureTypeError("Cannot convert %s to probability" % type(self))
  def getAtom(self): raise VentureTypeError("Cannot convert %s to atom" % type(self))
  def getBool(self): raise VentureTypeError("Cannot convert %s to bool" % type(self))
  def getSymbol(self): raise VentureTypeError("Cannot convert %s to symbol" % type(self))
  def getForeignBlob(self): raise VentureTypeError("Cannot convert %s to foreign blob" % type(self))
  def getPair(self): raise VentureTypeError("Cannot convert %s to pair" % type(self))
  # Convention for containers: if the elt_type argument is None,
  # return a Python container of VentureValue objects.  Otherwise,
  # apply the transformation given by the given type to the elements.
  def getArray(self, _elt_type=None): raise VentureTypeError("Cannot convert %s to array" % type(self))
  def getSimplex(self): raise VentureTypeError("Cannot convert %s to simplex" % type(self))
  def getDict(self): raise VentureTypeError("Cannot convert %s to dict" % type(self))
  def getMatrix(self): raise VentureTypeError("Cannot convert %s to matrix" % type(self))
  def getSymmetricMatrix(self): raise VentureTypeError("Cannot convert %s to symmetric matrix" % type(self))
  def getSP(self): raise VentureTypeError("Cannot convert %s to sp" % type(self))
  def getEnvironment(self): raise VentureTypeError("Cannot convert %s to environment" % type(self))

  ### Stack representation
  def asStackDict(self, _trace=None): raise Exception("Cannot convert %s to a stack dictionary" % type(self))
  @staticmethod
  def fromStackDict(thing):
    if isinstance(thing, list):
      # TODO Arrays or lists?
      return VentureArray([VentureValue.fromStackDict(val) for val in thing])
    else:
      t = thing["type"]
      if t not in stackable_types:
        raise VentureTypeError('Invalid type "%s"' % t)
      return stackable_types[t].fromStackDict(thing)

  ### Comparison
  def compare(self, other):
    st = type(self)
    ot = type(other)
    if st == ot:
      return self.compareSameType(other)
    if venture_types.index(st) < venture_types.index(ot) : return -1
    else: return 1 # We already checked for equality
  def compareSameType(self, _): raise Exception("Cannot compare %s" % type(self))
  def equal(self, other):
    st = type(self)
    ot = type(other)
    if st == ot:
      return self.equalSameType(other)
    else:
      return False
  def equalSameType(self, other): return self.compareSameType(other) == 0

  ### Generic container methods
  def lookup(self, _): raise VentureTypeError("Cannot look things up in %s" % type(self))
  def lookup_grad(self, _index, _direction):
    raise VentureTypeError("Cannot compute gradient of looking things up in %s" % type(self))
  def contains(self, _): raise VentureTypeError("Cannot look for things in %s" % type(self))
  def length(self): raise VentureTypeError("Cannot measure length of %s" % type(self))
  def take(self, _ct): raise VentureTypeError("Cannot take a prefix of %s" % type(self))

  def __eq__(self, other):
    if isinstance(other, VentureValue):
      return self.equal(other)
    else:
      return False
  
  def __ne__(self, other):
    return not self == other

  # Some Venture value types form a natural vector space over reals,
  # so overload addition, subtraction, and multiplication by scalars.
  # def __add__(self, other), and also __radd__, __neg__, __sub__,
  # __mul__, __rmul__, and dot

  # All Venture values have a (possibly trivial) cotangent space.  The
  # cotangent space is exposed through map_real, which constructs a
  # cotangent for a value given a function to which to feed the
  # value's current value at every dimension.
  def map_real(self, _f): return 0

  def expressionFor(self):
    return v.quote(self.asStackDict(None))

  def isValidCompoundForm(self): return False

def vv_dot_product(v1, v2):
  """Dot product of venture values taking into account that either may be
a symbolic zero.  TODO: Introduce the VentureZero value to uniformize
this."""
  if v1 is 0 or v2 is 0: return 0
  return v1.dot(v2)

class VentureNumber(VentureValue):
  def __init__(self,number):
    if not isinstance(number, Number):
      raise VentureTypeError("%s is of %s, not Number" % (str(number), type(number)))
    self.number = float(number)
  def __repr__(self):
    if hasattr(self, "number"):
      return "VentureNumber(%s)" % self.number
    else:
      return "VentureNumber(uninitialized)"
  def getNumber(self): return self.number
  def getInteger(self): return int(self.number)
  def getProbability(self):
    if 0 <= self.number and self.number <= 1:
      return self.number
    else: # TODO Do what?  Clip to [0,1]?  Raise?
      raise VentureTypeError("Probability out of range %s" % self.number)
  def getBool(self): return self.number

  def asStackDict(self, _trace=None): return v.number(self.number)
  @staticmethod
  def fromStackDict(thing): return VentureNumber(thing["value"])
  def compareSameType(self, other): return stupidCompare(self.number, other.number)
  def __hash__(self): return hash(self.number)
  def __add__(self, other):
    if other == 0:
      return self
    else:
      return VentureNumber(self.number + other.number)
  def __radd__(self, other):
    if other == 0:
      return self
    else:
      return VentureNumber(other.number + self.number)
  def __neg__(self):
    return VentureNumber(-self.number)
  def __sub__(self, other):
    if other == 0:
      return self
    else:
      return VentureNumber(self.number - other.number)
  def __mul__(self, other):
    # Assume other is a scalar
    assert isinstance(other, Number)
    return VentureNumber(self.number * other)
  def __rmul__(self, other):
    # Assume other is a scalar
    assert isinstance(other, Number)
    return VentureNumber(other * self.number)
  def __abs__(self):
    return VentureNumber(abs(self.number))
  def __float__(self):
    # Returns a Python number. Implemented for testing. assert_not_equal
    # calls round(), which in turn calls float()
    return self.number
  def dot(self, other):
    assert isinstance(other, VentureNumber)
    return self.number * other.number
  def map_real(self, f):
    return VentureNumber(f(self.number))
  def real_lenses(self):
    class NumberLens(MLens):
      # Poor man's closure: pass the relevant thing from the lexical
      # scope directly.
      def __init__(self, vn):
        self.vn = vn
      def get(self):
        return self.vn.number
      def set(self, new):
        assert isinstance(new, Number)
        self.vn.number = new
    return [NumberLens(self)]
  def expressionFor(self): return self.number

class VentureInteger(VentureValue):
  def __init__(self,number):
    assert isinstance(number, Number)
    self.number = int(number)
  def __repr__(self):
    if hasattr(self, "number"):
      return "VentureInteger(%s)" % self.number
    else:
      return "VentureInteger(uninitialized)"
  def getInteger(self): return self.number
  def getNumber(self): return float(self.number)
  def getBool(self): return self.number
  def asStackDict(self, _trace=None): return v.integer(self.number)
  @staticmethod
  def fromStackDict(thing): return VentureInteger(thing["value"])
  def compareSameType(self, other): return stupidCompare(self.number, other.number)
  def __hash__(self): return hash(self.number)
  def expressionFor(self): return self.number

class VentureProbability(VentureValue):
  def __init__(self, number):
    assert isinstance(number, Number)
    assert 0 <= number and number <= 1
    self.number = float(number)
  def __repr__(self):
    if hasattr(self, "number"):
      return "VentureProbability(%s)" % self.number
    else:
      return "VentureProbability(uninitialized)"
  def getNumber(self): return self.number
  def getProbability(self): return self.number
  def asStackDict(self, _trace=None): return v.probability(self.number)
  @staticmethod
  def fromStackDict(thing): return VentureProbability(thing["value"])
  def compareSameType(self, other): return stupidCompare(self.number, other.number)
  def __hash__(self): return hash(self.number)
  def expressionFor(self):
    return [v.symbol("probability"), self.number]
  def map_real(self, f):
    return VentureNumber(f(self.number))
  def real_lenses(self):
    class NumberLens(MLens):
      # Poor man's closure: pass the relevant thing from the lexical
      # scope directly.
      def __init__(self, vn):
        self.vn = vn
      def get(self):
        return self.vn.number
      def set(self, new):
        assert isinstance(new, Number)
        self.vn.number = new
    return [NumberLens(self)]

def stupidCompare(thing, other):
  # number.__cmp__(other) works for ints but not floats.  Guido, WTF!?
  # strings don't have __cmp__ either? or lists?
  if thing < other: return -1
  elif thing > other: return 1
  else: return 0

def lexicographicBoxedCompare(thing, other):
  if len(thing) < len(other): return -1
  if len(thing) > len(other): return 1

  # else same length
  for x,y in zip(thing,other):
    if x.compare(y) != 0: return x.compare(y)

  return 0

def lexicographicUnboxedCompare(thing, other):
  if len(thing) < len(other): return -1
  if len(thing) > len(other): return 1

  # else same length
  for x,y in zip(thing,other):
    if stupidCompare(x,y) != 0: return stupidCompare(x,y)

  return 0

def lexicographicMatrixCompare(thing, other):
  ct_thing = reduce(operator.mul, np.shape(thing), 1)
  ct_other = reduce(operator.mul, np.shape(other), 1)
  if ct_thing == 0 and ct_other == 0: return 0
  shape_cmp = lexicographicUnboxedCompare(np.shape(thing), np.shape(other))
  if not shape_cmp == 0: return shape_cmp

  # else shame shape
  if np.array_equal(thing, other): return 0
  # Hack for finding the first discrepant element, via
  # http://stackoverflow.com/questions/432112/is-there-a-numpy-function-to-return-the-first-index-of-something-in-an-array
  diffs = np.array(thing - other)
  diff_indexes = np.nonzero(diffs)
  first_diff = diffs[diff_indexes[0][0]][diff_indexes[0][0]]
  return stupidCompare(first_diff, 0)

def sequenceHash(seq):
  return reduce(lambda res, item: res * 37 + item, [hash(i) for i in seq], 1)

class VentureAtom(VentureValue):
  def __init__(self,atom):
    assert isinstance(atom, Number)
    self.atom = atom
  def __repr__(self): return "Atom(%s)" % self.atom
  def getNumber(self): return self.atom
  def getAtom(self): return self.atom
  def getBool(self): return self.atom
  def asStackDict(self, _trace=None): return v.atom(self.atom)
  @staticmethod
  def fromStackDict(thing): return VentureAtom(thing["value"])
  def compareSameType(self, other): return stupidCompare(self.atom, other.atom)
  def __hash__(self): return hash(self.atom)
  def expressionFor(self): return v.quote(self) # TODO Is this right?

class VentureBool(VentureValue):
  def __init__(self,boolean):
    assert isinstance(boolean, bool) or isinstance(boolean, np.bool_)
    self.boolean = bool(boolean)
  def __repr__(self): return "Bool(%s)" % self.boolean
  def getBool(self): return self.boolean
  def getNumber(self):
    # TODO This horrible thing permits adding the outputs of bernoulli
    # trials as well as dispatching on them.  Or should flip and
    # bernoulli be different SPs?
    return self.boolean
  def getInteger(self): return self.boolean
  def asStackDict(self, _trace=None): return v.boolean(self.boolean)
  @staticmethod
  def fromStackDict(thing): return VentureBool(thing["value"])
  def compareSameType(self, other):
    return stupidCompare(self.boolean, other.boolean)
  def __hash__(self): return hash(self.boolean)
  def expressionFor(self):
    return v.symbol("true") if self.boolean else v.symbol("false")

class VentureSymbol(VentureValue):
  def __init__(self,symbol): self.symbol = symbol
  def __repr__(self): return "Symbol(%s)" % self.symbol
  def getSymbol(self): return self.symbol
  def asStackDict(self, _trace=None): return v.symbol(self.symbol)
  @staticmethod
  def fromStackDict(thing): return VentureSymbol(thing["value"])
  def compareSameType(self, other): return stupidCompare(self.symbol, other.symbol)
  def __hash__(self): return hash(self.symbol)
  def expressionFor(self): return v.quote(self.asStackDict(None))

class VentureForeignBlob(VentureValue):
  # TODO Think about the interaction of foreign blobs with trace
  # copying and serialization
  def __init__(self, datum): self.datum = datum

  def getForeignBlob(self): return self.datum

  def asStackDict(self, _trace=None):
    return v.blob(self.datum)
  @staticmethod
  def fromStackDict(thing): return VentureForeignBlob(thing["value"])

class VentureNil(VentureValue):
  def __init__(self): pass
  def __repr__(self): return "Nil"

  def getArray(self, elt_type=None):
    return VentureArray([]).getArray(elt_type)

  def asStackDict(self, _trace=None): return v.list([])
  @staticmethod
  def fromStackDict(_): return VentureNil()

  def compareSameType(self, _): return 0 # All Nils are equal
  def __hash__(self): return 0

  def lookup(self, index):
    raise VentureValueError("Index out of bounds: too long by %s" % index)
  def contains(self, _obj): return False
  def size(self): return 0
  def take(self, ct):
    if ct < 1:
      return self
    else:
      raise VentureValueError("Index out of bounds: too long by %s" % ct)

  def expressionFor(self):
    return [v.symbol("list")]

  def isValidCompoundForm(self): return True
  def asPossiblyImproperList(self): return ([], None)
  def asPythonList(self, _elt_type=None): return []

class VenturePair(VentureValue):
  def __init__(self,(first,rest)):
    # TODO Maybe I need to be careful about tangent and cotangent
    # spaces after all.  A true pair needs to have a venture value
    # inside; a pair that represents the cotangent of something needs
    # to have cotangents; but cotangents permit symbolic zeros.
    if not first == 0: assert isinstance(first, VentureValue)
    if not rest == 0:  assert isinstance(rest, VentureValue)
    self.first = first
    self.rest = rest
  def __repr__(self):
    (list_, tail) = self.asPossiblyImproperList()
    if tail is None:
      return "VentureList(%r)" % list_
    else:
      return "VentureList(%r . %r)" % (list_, tail)

  def getPair(self): return (self.first,self.rest)
  def getArray(self, elt_type=None):
    (list_, tail) = self.asPossiblyImproperList()
    if tail is None:
      return VentureArray(list_).getArray(elt_type)
    else:
      raise Exception("Cannot convert an improper list to array")

  def asStackDict(self, trace=None):
    (list_, tail) = self.asPossiblyImproperList()
    if tail is None:
      return v.list([val.asStackDict(trace) for val in list_])
    else:
      return v.improper_list([val.asStackDict(trace) for val in list_], tail.asStackDict())
  @staticmethod
  def fromStackDict(thing):
    if thing["type"] == "improper_list":
      (list_, tail) = thing["value"]
      return pythonListToImproperVentureList(VentureValue.fromStackDict(tail),
                                             *[VentureValue.fromStackDict(val) for val in list_])
    else:
      return pythonListToVentureList([VentureValue.fromStackDict(val) for val in thing["value"]])

  def compareSameType(self, other):
    fstcmp = self.first.compare(other.first)
    if fstcmp != 0: return fstcmp
    else: return self.rest.compare(other.rest)
  def __hash__(self):
    return hash(self.first) + 37*hash(self.rest)

  def lookup(self, index):
    try:
      ind = index.getNumber()
    except VentureTypeError:
      raise VentureValueError("Looking up non-number %r in a list" % index)
    if ind < 1: # Equivalent to truncating for positive floats
      return self.first
    else:
      return self.rest.lookup(VentureNumber(ind - 1))
  def lookup_grad(self, index, direction):
    if direction == 0: return 0
    try:
      ind = index.getNumber()
    except VentureTypeError:
      raise VentureValueError("Looking up non-number %r in a list" % index)
    if ind < 1:
      return VenturePair((direction, 0))
    else:
      return VenturePair((0, self.rest.lookup_grad(VentureNumber(ind - 1), direction)))
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
  def take(self, ind):
    if ind < 1:
      return VentureNil()
    else:
      return VenturePair(self.first, self.rest.take(ind-1))

  def __add__(self, other):
    if other == 0:
      return self
    else:
      return VenturePair((self.first + other.first, self.rest + other.rest))
  def __radd__(self, other):
    if other == 0:
      return self
    else:
      return VenturePair((other.first + self.first, other.rest + self.rest))
  def __neg__(self):
    return VenturePair((-self.first, -self.rest))
  def __sub__(self, other):
    if other == 0:
      return self
    else:
      return VenturePair((self.first - other.first, self.rest - other.rest))
  def __mul__(self, other):
    # Assume other is a scalar
    assert isinstance(other, Number)
    return VenturePair((self.first * other, self.rest * other))
  def __rmul__(self, other):
    # Assume other is a scalar
    assert isinstance(other, Number)
    return VenturePair((other * self.first, other * self.rest))
  def dot(self, other):
    return vv_dot_product(self.first, other.first) + vv_dot_product(self.rest, other.rest)
  def map_real(self, f):
    return VenturePair((self.first.map_real(f), self.rest.map_real(f)))

  def expressionFor(self):
    return [v.symbol("pair"), self.first.expressionFor(), self.rest.expressionFor()]

  def isValidCompoundForm(self):
    return self.rest.isValidCompoundForm()
  def asPythonList(self, elt_type=None):
    if elt_type is not None:
      return [elt_type.asPython(self.first)] + self.rest.asPythonList(elt_type)
    else:
      return [self.first] + self.rest.asPythonList()
  def asPossiblyImproperList(self):
    if isinstance(self.rest, VenturePair):
      (sublist, tail) = self.rest.asPossiblyImproperList()
      return ([self.first] + sublist, tail)
    elif isinstance(self.rest, VentureNil):
      return ([self.first], None)
    else:
      return ([self.first], self.rest)

def pythonListToVentureList(l):
  return reduce(lambda t, h: VenturePair((h, t)), reversed(l), VentureNil())

def pythonListToImproperVentureList(tail, *l):
  return reduce(lambda t, h: VenturePair((h, t)), reversed(l), tail)

class VentureArray(VentureValue):
  """Venture arrays are heterogeneous, with O(1) access and O(n) copy."""
  def __init__(self, array): self.array = array
  def __repr__(self):
    return "VentureArray(%s)" % self.array
  def getArray(self, elt_type=None):
    if elt_type is None: # No conversion
      return self.array
    else:
      return [elt_type.asPython(val) for val in self.array]

  def compareSameType(self, other):
    return lexicographicBoxedCompare(self.array, other.array)
  def __hash__(self): return sequenceHash(self.array)

  def asStackDict(self, trace=None):
    return v.array([val.asStackDict(trace) for val in self.array])
  @staticmethod
  def fromStackDict(thing):
    return VentureArray([VentureValue.fromStackDict(val) for val in thing["value"]])

  def lookup(self, index):
    try:
      ind = index.getNumber()
    except VentureTypeError:
      raise VentureValueError("Looking up non-number %r in an array" % index)
    if 0 <= int(ind) and int(ind) < len(self.array):
      return self.array[int(ind)]
    else:
      raise VentureValueError("Index out of bounds: %s" % index)
  def lookup_grad(self, index, direction):
    return VentureArray([direction if i == index else 0 for (_,i) in enumerate(self.array)])
  def contains(self, obj):
    # Not Python's `in` because I need to use custom equality
    # TODO I am going to have to overload the equality for dicts
    # anyway, so might as well eventually use `in` here.
    return any(obj.equal(li) for li in self.array)
  def size(self): return len(self.array)
  def take(self, ind):
    return VentureArray(self.array[0:ind])

  def __add__(self, other):
    if other == 0:
      return self
    else:
      return VentureArray([x + y for (x,y) in zip(self.array, other.array)])
  def __radd__(self, other):
    if other == 0:
      return self
    else:
      return VentureArray([y + x for (x,y) in zip(self.array, other.array)])
  def __neg__(self):
    return VentureArray([-x for x in self.array])
  def __sub__(self, other):
    if other == 0:
      return self
    else:
      return VentureArray([x - y for (x,y) in zip(self.array, other.array)])
  def __mul__(self, other):
    # Assume other is a scalar
    assert isinstance(other, Number)
    return VentureArray([x * other for x in self.array])
  def __rmul__(self, other):
    # Assume other is a scalar
    assert isinstance(other, Number)
    return VentureArray([other * x  for x in self.array])
  def dot(self, other):
    return sum([vv_dot_product(x, y) for (x,y) in zip(self.array, other.array)])
  def map_real(self, f):
    return VentureArray([x.map_real(f) for x in self.array])

  def expressionFor(self):
    return [v.symbol("array")] + [val.expressionFor() for val in self.array]

  def isValidCompoundForm(self): return True
  def asPythonList(self, elt_type=None):
    return self.getArray(elt_type)

class VentureArrayUnboxed(VentureValue):
  """Venture arrays of unboxed objects are homogeneous, with O(1) access and O(n) copy."""
  def __init__(self, array, elt_type):
    from types import VentureType
    if not isinstance(elt_type, VentureType):
      raise VentureTypeError("%s of %s is not a VentureType" % (elt_type, type(elt_type)))
    self.elt_type = elt_type
    self.array = enp.ensure_numpy_if_possible(elt_type, array)
  def __repr__(self):
    return "VentureArrayUnboxed(%s)" % self.array

  # This method produces results that are at least Python-boxed
  def getArray(self, elt_type=None):
    if elt_type is None: # Convert to VentureValue
      return [self.elt_type.asVentureValue(val) for val in self.array]
    else:
      # TODO What I really need here is the function that converts
      # from the Python representation of self.elt_type to the Python
      # representation of elt_type, with an optimization if that
      # function is the identity.
      if elt_type == self.elt_type:
        return self.array
      else:
        return [elt_type.asPython(self.elt_type.asVentureValue(val)) for val in self.array]

  def compareSameType(self, other):
    return lexicographicUnboxedCompare(self.array, other.array)
  def __hash__(self): return sequenceHash(self.array)

  def asStackDict(self,_trace=None):
    return v.array_unboxed(self.array, self.elt_type)
  @staticmethod
  def fromStackDict(thing):
    if thing["type"] == "vector":
      # TODO HACK: treat Puma's vectors as unboxed arrays of numbers,
      # because Puma can't make a NumberType to stick in the stack
      # dict.
      from types import NumberType
      return VentureArrayUnboxed(thing["value"], NumberType())
    return VentureArrayUnboxed(thing["value"], thing["subtype"])

  def lookup(self, index):
    try:
      ind = index.getNumber()
    except VentureTypeError:
      raise VentureValueError("Looking up non-number %r in an array" % index)
    if 0 <= int(ind) and int(ind) < len(self.array):
      return self.elt_type.asVentureValue(self.array[int(ind)])
    else:
      raise VentureValueError("Index out of bounds: %s" % index)
  def lookup_grad(self, index, direction):
    # TODO Really this should be an unboxed array of the gradient
    # types of the elements, with generic zeroes.
    return VentureArray([direction if i == index else 0 for (_,i) in enumerate(self.array)])
  def contains(self, obj):
    return any(obj.equal(self.elt_type.asVentureValue(li)) for li in self.array)
  def size(self): return len(self.array)
  def take(self, ind):
    return VentureArrayUnboxed(self.array[0:ind], self.elt_type)

  def __add__(self, other):
    if other == 0:
      return self
    else:
      return VentureArrayUnboxed(*enp.map2(operator.add, self.array, self.elt_type, other.array, other.elt_type))
  def __radd__(self, other):
    if other == 0:
      return self
    else:
      return VentureArrayUnboxed(*enp.map2(operator.add, other.array, other.elt_type, self.array, self.elt_type))
  def __neg__(self):
    return VentureArrayUnboxed(enp.map(operator.neg, self.array, self.elt_type), self.elt_type)
  def __sub__(self, other):
    if other == 0:
      return self
    else:
      return VentureArrayUnboxed(*enp.map2(operator.sub, self.array, self.elt_type, other.array, other.elt_type))
  def __mul__(self, other):
    # Assume other is a scalar
    assert isinstance(other, Number)
    return VentureArrayUnboxed(enp.map(lambda x: x * other, self.array, self.elt_type), self.elt_type)
  def __rmul__(self, other):
    # Assume other is a scalar
    assert isinstance(other, Number)
    return VentureArrayUnboxed(enp.map(lambda x: other * x, self.array, self.elt_type), self.elt_type)
  def dot(self, other):
    return enp.dot(self.array, self.elt_type, other.array, other.elt_type)
  def map_real(self, f):
    # TODO Ascertain whether self.elt_type represents a real number or not so I can do
    # return VentureArrayUnboxed(enp.map(f, self.array, self.elt_type), self.elt_type)
    # but the general case is
    new_type = self.elt_type.gradient_type()
    new_data = [new_type.asPython(self.elt_type.asVentureValue(val).map_real(f)) for val in self.array]
    return VentureArrayUnboxed(new_data, new_type)

  def isValidCompoundForm(self): return False
  def asPythonList(self, elt_type=None):
    return self.getArray(elt_type)

class VentureSimplex(VentureValue):
  """Simplexes are homogeneous unboxed arrays of probabilities.  They
are also supposed to sum to 1, but we are not checking that.

  """
  def __init__(self,simplex): self.simplex = simplex
  def __repr__(self):
    return "VentureSimplex(%s)" % self.simplex
  def getArray(self, elt_type=None):
    from types import ProbabilityType
    # TODO Abstract similarities between this and the getArray method of ArrayUnboxed
    if elt_type is None: # Convert to VentureValue
      return [ProbabilityType().asVentureValue(val) for val in self.simplex]
    else:
      if elt_type.__class__ == ProbabilityType:
        return self.simplex
      else:
        return [elt_type.asPython(ProbabilityType().asVentureValue(val)) for val in self.simplex]
  def getSimplex(self): return self.simplex

  def compareSameType(self, other):
    # The Python ordering is lexicographic first, then by length, but
    # I think we want lower-d simplexes to compare less than higher-d
    # ones regardless of the point.
    return lexicographicUnboxedCompare(self.simplex, other.simplex)
  def __hash__(self):
    return sequenceHash(self.simplex)

  def asStackDict(self, _trace=None):
    # TODO As what type to reflect simplex points to the stack?
    return v.simplex(self.simplex)
  @staticmethod
  def fromStackDict(thing): return VentureSimplex(thing["value"])

  def lookup(self, index):
    from types import ProbabilityType
    return ProbabilityType().asVentureValue(self.simplex[index.getNumber()])
  def contains(self, obj):
    # Homogeneous; TODO make it return False instead of exploding for non-numeric objects.
    return obj.getNumber() in self.simplex
  def size(self): return len(self.simplex)
  def take(self, ind):
    from types import ProbabilityType
    return VentureArrayUnboxed(self.simplex[0:ind], ProbabilityType())

  def expressionFor(self):
    return [v.symbol("simplex")] + self.simplex
  def map_real(self, f):
    # The cotangent space actually has the constraint that the cotangents sum to 0
    from types import NumberType
    return VentureArrayUnboxed([f(p) for p in self.simplex], NumberType())

class VentureDict(VentureValue):
  def __init__(self,d): self.dict = d

  def getDict(self): return self.dict

  def asStackDict(self, _trace=None):
    return v.dict([(key.asStackDict(_trace), val.asStackDict(_trace)) for (key, val) in self.dict.items()])
  @staticmethod
  def fromStackDict(thing):
    f = VentureValue.fromStackDict
    return VentureDict({f(key):f(val) for (key, val) in thing["value"]})

  def equalSameType(self, other):
    return len(set(self.dict.iteritems()) ^ set(other.dict.iteritems())) == 0

  def lookup(self, key):
    return self.dict[key]
  def contains(self, key):
    return key in self.dict
  def size(self): return len(self.dict)

  def expressionFor(self):
    (keys, vals) = zip(*self.dict.iteritems())
    return [v.symbol("dict"),
            [v.symbol("list")] + [key.expressionFor() for key in keys],
            [v.symbol("list")] + [val.expressionFor() for val in vals]]

# 2D array of numbers backed by a numpy array object
class VentureMatrix(VentureValue):
  def __init__(self,matrix): self.matrix = np.asarray(matrix)
  def __repr__(self):
    return "VentureMatrix(%s)" % self.matrix

  def getMatrix(self): return self.matrix
  def getSymmetricMatrix(self):
    if matrixIsSymmetric(self.matrix):
      return self.matrix
    else:
      raise VentureTypeError("Matrix is not symmetric %s" % self.matrix)

  def compareSameType(self, other):
    return lexicographicMatrixCompare(self.matrix, other.matrix)
  def __hash__(self):
    # From http://stackoverflow.com/questions/5386694/fast-way-to-hash-numpy-objects-for-caching
    b = self.matrix.view(np.uint8)
    return hash(hashlib.sha1(b).hexdigest())

  def asStackDict(self, _trace=None):
    return v.matrix(self.matrix)
  @staticmethod
  def fromStackDict(thing): return VentureMatrix(thing["value"])

  def lookup(self, index):
    try:
      (vind1, vind2) = index.getPair()
      ind1 = vind1.getNumber()
      ind2 = vind2.getNumber()
    except VentureTypeError:
      raise VentureValueError("Looking up non-pair-of-numbers %r in a matrix" % index)
    from types import NumberType
    return NumberType().asVentureValue(self.matrix[int(ind1), int(ind2)])

  def __add__(self, other):
    if other == 0:
      return self
    else:
      return VentureMatrix(self.matrix + other.matrix)
  def __radd__(self, other):
    if other == 0:
      return self
    else:
      return VentureMatrix(other.matrix + self.matrix)
  def __neg__(self):
    return VentureMatrix(-self.matrix)
  def __sub__(self, other):
    if other == 0:
      return self
    else:
      return VentureMatrix(self.matrix - other.matrix)
  def __mul__(self, other):
    # Assume other is a scalar
    assert isinstance(other, Number)
    return VentureMatrix(self.matrix * other)
  def __rmul__(self, other):
    # Assume other is a scalar
    assert isinstance(other, Number)
    return VentureMatrix(other * self.matrix)
  def dot(self, other):
    assert isinstance(other, VentureMatrix)
    return np.sum(np.multiply(self.matrix, other.matrix))
  def map_real(self, f):
    if self.matrix.size == 0: return self # Do I seriously have to special-case this?
    return VentureMatrix(np.vectorize(f)(self.matrix))

  def expressionFor(self):
    return [v.symbol("matrix"),
            [v.symbol("list")] + [[v.symbol("list")] + [val for val in row] for row in self.matrix]]

class VentureSymmetricMatrix(VentureMatrix):
  def __init__(self, matrix):
    self.matrix = np.asarray(matrix)
    assert matrixIsSymmetric(self.matrix)
  def __repr__(self):
    return "VentureSymmetricMatrix(%s)" % self.matrix

  def asStackDict(self, _trace=None):
    return v.symmetric_matrix(self.matrix)
  @staticmethod
  def fromStackDict(thing): return VentureSymmetricMatrix(thing["value"])

  def __add__(self, other):
    if other == 0:
      return self
    if isinstance(other, VentureSymmetricMatrix):
      return VentureSymmetricMatrix(self.matrix + other.matrix)
    else:
      return VentureMatrix(self.matrix + other.matrix)
  def __radd__(self, other):
    if other == 0:
      return self
    if isinstance(other, VentureSymmetricMatrix):
      return VentureSymmetricMatrix(other.matrix + self.matrix)
    else:
      return VentureMatrix(other.matrix + self.matrix)
  def __neg__(self):
    return VentureSymmetricMatrix(-self.matrix)
  def __sub__(self, other):
    if other == 0:
      return self
    if isinstance(other, VentureSymmetricMatrix):
      return VentureSymmetricMatrix(self.matrix - other.matrix)
    else:
      return VentureMatrix(self.matrix - other.matrix)
  def __mul__(self, other):
    # Assume other is a scalar
    assert isinstance(other, Number)
    return VentureSymmetricMatrix(self.matrix * other)
  def __rmul__(self, other):
    # Assume other is a scalar
    assert isinstance(other, Number)
    return VentureSymmetricMatrix(other * self.matrix)
  def map_real(self, f):
    if self.matrix.size == 0: return self # Do I seriously have to special-case this?
    candidate = np.vectorize(f)(self.matrix)
    return VentureSymmetricMatrix( (candidate + candidate.T)/2 )

  def expressionFor(self):
    return v.quote(self.asStackDict(None))

def matrixIsSymmetric(matrix):
  return np.allclose(matrix.transpose(), matrix)

class SPRef(VentureValue):
  def __init__(self,makerNode): self.makerNode = makerNode
  def asStackDict(self, trace=None):
    assert trace is not None
    return trace.madeSPRecordAt(self.makerNode).asStackDict()

  @staticmethod
  def fromStackDict(thing): return thing["value"]
  # SPRefs are intentionally not comparable until we decide otherwise

# Actually, Environments and SPs have cotangent spaces too, in their
# own funny way, but we're not doing that now.

## SPs and Environments as well
## Not Requests, because we do not reflect on them

venture_types = [
  VentureNumber, VentureInteger, VentureProbability, VentureAtom, VentureBool,
  VentureSymbol, VentureForeignBlob, VentureNil, VenturePair,
  VentureArray, VentureArrayUnboxed, VentureSimplex, VentureDict, VentureMatrix,
  VentureSymmetricMatrix, SPRef]
  # Break load order dependency by not adding SPs and Environments yet

stackable_types = {
  "number": VentureNumber,
  "real": VentureNumber,
  "integer": VentureInteger,
  "probability": VentureProbability,
  "atom": VentureAtom,
  "boolean": VentureBool,
  "symbol": VentureSymbol,
  "blob": VentureForeignBlob,
  "list": VenturePair,
  "improper_list": VenturePair,
  "vector": VentureArrayUnboxed,
  "array": VentureArray,
  "array_unboxed": VentureArrayUnboxed,
  "simplex": VentureSimplex,
  "dict": VentureDict,
  "matrix": VentureMatrix,
  "symmetric_matrix": VentureSymmetricMatrix,
  "SP": SPRef, # As opposed to VentureSPRecord?
  }

def registerVentureType(t, name = None):
  if t in venture_types: pass
  else:
    venture_types.append(t)
    if name is not None:
      stackable_types[name] = t

