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

import numbers

import numpy as np

import venture.lite.value as vv
import venture.lite.request as req

# No, pylint, I really do mean to check whether two objects have the
# same type.
# pylint:disable=unidiomatic-typecheck

### Venture Types

class VentureType(object):
  """Base class of all Venture types.

See the "Types" section of doc/type-system.md."""
  def asPythonNoneable(self, vthing):
    if vthing is None:
      return None
    else:
      # Function will be added by inheritance pylint:disable=no-member
      return self.asPython(vthing)
  def distribution(self, base, **kwargs):
    return base(self.name()[1:-1], **kwargs) # Strip the angle brackets
  def __eq__(self, other):
    return type(self) == type(other)

  def gradient_type(self):
    "The type of the cotangent space of the space represented by this type."
    return self

  def toJSON(self):
    return self.__class__.__name__

# TODO Is there any way to make these guys be proper singleton
# objects?

class AnyType(VentureType):
  """The type object to use for parametric types -- does no conversion."""
  def __init__(self, type_name=None):
    self.type_name = type_name
  def asVentureValue(self, thing):
    assert isinstance(thing, vv.VentureValue)
    return thing
  def asPython(self, thing):
    # TODO Make symbolic zeroes a venture value!
    assert isinstance(thing, vv.VentureValue) or thing is 0
    return thing
  def __contains__(self, vthing): return isinstance(vthing, vv.VentureValue)
  def name(self):
    if self.type_name is None:
      return "<object>"
    else:
      return self.type_name
  def distribution(self, base, **kwargs):
    return base("object", **kwargs)

# This is a prototypical example of the classes I am autogenerating
# below, for legibility.  I could have removed this and added "Number"
# to the list in the for.
class NumberType(VentureType):
  def __init__(self, name=None):
    self._name = name
  def asVentureValue(self, thing): return vv.VentureNumber(thing)
  def asPython(self, vthing): return vthing.getNumber()
  def __contains__(self, vthing): return isinstance(vthing, vv.VentureNumber)
  def name(self): return self._name or "<number>"

def standard_venture_type(typename, gradient_typename=None, value_classname=None):
  if gradient_typename is None:
    gradient_typename = typename
  if value_classname is None:
    value_classname = "vv.Venture%s" % (typename,)
  return """
class %sType(VentureType):
  def __init__(self, name=None):
    self._name = name
  def asVentureValue(self, thing): return %s(thing)
  def asPython(self, vthing): return vthing.get%s()
  def __contains__(self, vthing): return isinstance(vthing, %s)
  def name(self): return self._name or "<%s>"
  def gradient_type(self): return %sType()
""" % (typename, value_classname, typename, value_classname, typename.lower(),
       gradient_typename)

for typename in ["Integer", "Atom", "Bool", "Symbol", "String", "ForeignBlob"]:
  # Exec is appropriate for metaprogramming, but indeed should not be
  # used lightly.
  # pylint: disable=exec-used
  exec(standard_venture_type(typename, gradient_typename="Zero"))

for typename in ["Array", "Simplex", "Dict", "Matrix", "SymmetricMatrix"]:
  # Exec is appropriate for metaprogramming, but indeed should not be
  # used lightly.
  # pylint: disable=exec-used
  exec(standard_venture_type(typename))

# Exec is appropriate for metaprogramming, but indeed should not be
# used lightly.
# pylint: disable=exec-used
exec(standard_venture_type("Probability", gradient_typename="Number"))

class CountType(VentureType):
  def __init__(self, name=None):
    self._name = name
  def asVentureValue(self, thing):
    assert thing >= 0
    return vv.VentureInteger(thing)
  def asPython(self, vthing):
    ans = vthing.getInteger()
    if ans >= 0:
      return ans
    else:
      # TODO: Or what?  Clip to 0?
      raise vv.VentureTypeError("Count is not positive %s" % self.number)
  def __contains__(self, vthing):
    return isinstance(vthing, vv.VentureInteger) and vthing.getInteger() >= 0
  def name(self): return self._name or "<count>"
  def gradient_type(self): return ZeroType()

class PositiveType(VentureType):
  def __init__(self, name=None):
    self._name = name
  def asVentureValue(self, thing):
    assert thing > 0
    return vv.VentureNumber(thing)
  def asPython(self, vthing):
    ans = vthing.getNumber()
    if ans > 0:
      return ans
    else:
      # TODO: Or what?  Can't even clip to 0!
      raise vv.VentureTypeError("Number is not positive %s" % ans)
  def __contains__(self, vthing):
    return isinstance(vthing, vv.VentureNumber) and vthing.getNumber() > 0
  def name(self): return self._name or "<positive>"
  def gradient_type(self): return NumberType()

class NilType(VentureType):
  def __init__(self, name=None):
    self._name = name
  def asVentureValue(self, _thing):
    # TODO Throw an error if not null-like?
    return vv.VentureNil()
  def asPython(self, _vthing):
    # TODO Throw an error if not nil?
    return []
  def __contains__(self, vthing): return isinstance(vthing, vv.VentureNil)
  def name(self): return self._name or "()"
  def distribution(self, base, **kwargs):
    return base("nil", **kwargs)

class PairType(VentureType):
  def __init__(self, first_type=None, second_type=None, name=None):
    self.first_type = first_type if first_type is not None else AnyType()
    self.second_type = second_type if second_type is not None else AnyType()
    self._name = name
  def asVentureValue(self, thing):
    (f, r) = thing
    return vv.VenturePair((self.first_type.asVentureValue(f),
                           self.second_type.asVentureValue(r)))
  def asPython(self, vthing):
    (vf, vr) = vthing.getPair()
    return (self.first_type.asPython(vf), self.second_type.asPython(vr))
  def __contains__(self, vthing): return isinstance(vthing, vv.VenturePair)
  def name(self):
    if self._name is not None:
      return self._name
    if self.first_type is None and self.second_type is None:
      return "<pair>"
    first_name = self.first_type.name() if self.first_type else "<object>"
    second_name = self.second_type.name() if self.second_type else "<object>"
    return "<pair %s %s>" % (first_name, second_name)
  def distribution(self, base, **kwargs):
    first_dist = self.first_type.distribution(base, **kwargs) \
                 if self.first_type else None
    second_dist = self.second_type.distribution(base, **kwargs) \
                  if self.second_type else None
    return base("pair", first_dist=first_dist, second_dist=second_dist,
                **kwargs)

class ListType(VentureType):
  """A Venture list is either a VentureNil or a VenturePair whose
second field is a Venture list.  I choose that the corresponding
Python object is a list of VentureValue objects (this is consistent
with the Any type doing no conversion).

In Haskell type notation:

data List = Nil | Pair Any List
"""
  def __init__(self, name=None):
    self._name = name
  def asVentureValue(self, thing):
    return vv.pythonListToVentureList(thing)
  def asPython(self, thing):
    return thing.asPythonList()
  def __contains__(self, vthing):
    return isinstance(vthing, vv.VentureNil) \
      or (isinstance(vthing, vv.VenturePair) and vthing.rest in self)
  def name(self): return self._name or "<list>"

class HomogeneousListType(VentureType):
  """Type objects for homogeneous lists.  Right now, the homogeneity
  is not captured in the implementation, in that on the Venture side
  such data is still stored as heterogenous Venture lists.  This type
  does, however, encapsulate the necessary wrapping and unwrapping."""
  def __init__(self, subtype, name = None):
    assert isinstance(subtype, VentureType)
    self.subtype = subtype
    self._name = name
  def asVentureValue(self, thing):
    return vv.pythonListToVentureList([self.subtype.asVentureValue(t)
                                       for t in thing])
  def asPython(self, vthing):
    return vthing.asPythonList(self.subtype)
  def __contains__(self, vthing):
    return vthing in ListType() \
      and all([val in self.subtype for val in vthing.asPythonList()])
  def __eq__(self, other):
    return type(self) == type(other) and self.subtype == other.subtype
  def name(self): return self._name or "<list %s>" % self.subtype.name()
  def distribution(self, base, **kwargs):
    # TODO Is this splitting what I want?
    return base("list", elt_dist=self.subtype.distribution(base, **kwargs),
                **kwargs)

class ArrayUnboxedType(VentureType):
  """Type objects for arrays of unboxed values.  Perforce homogeneous."""
  def __init__(self, subtype, name = None):
    assert isinstance(subtype, VentureType)
    self.subtype = subtype
    self._name = name
  def asVentureValue(self, thing):
    return vv.VentureArrayUnboxed(thing, self.subtype)
  def asPython(self, vthing):
    return vthing.getArray(self.subtype)
  def __contains__(self, vthing):
    # TODO Need a more general element type compatibility check
    unboxed = isinstance(vthing, vv.VentureArrayUnboxed) \
              and vthing.elt_type == self.subtype
    boxed = isinstance(vthing, vv.VentureArray) \
            and all([val in self.subtype for val in vthing.getArray()])
    return unboxed or boxed
  def __eq__(self, other):
    return type(self) == type(other) and self.subtype == other.subtype
  def name(self): return self._name or "<array %s>" % self.subtype.name()
  def distribution(self, base, **kwargs):
    return base("array_unboxed", elt_type=self.subtype, **kwargs)
  def gradient_type(self): return ArrayUnboxedType(self.subtype.gradient_type())

HomogeneousArrayType = ArrayUnboxedType

class HomogeneousSequenceType(VentureType):
  """Type objects for homogeneous sequences of any persuasion (lists,
  arrays, vectors, simplexes).  Right now, the homogeneity is not
  captured in the implementation, in that on the Venture side such
  data is still stored as heterogenous Venture arrays.  This type is
  purely advisory and does not do any conversion.

  """
  def __init__(self, subtype, name = None):
    assert isinstance(subtype, VentureType)
    self.subtype = subtype
    self._name = name
  def asVentureValue(self, thing):
    return thing
  def asPython(self, vthing):
    return vthing
  def __contains__(self, vthing):
    return (isinstance(vthing, vv.VentureArray) \
            or isinstance(vthing, vv.VentureSimplex) \
            or isinstance(vthing, vv.VentureArrayUnboxed) \
            or vthing in ListType()) \
      and all([val in self.subtype for val in vthing.getArray()])
  def __eq__(self, other):
    return type(self) == type(other) and self.subtype == other.subtype
  def name(self): return self._name or "<sequence %s>" % self.subtype.name()
  def distribution(self, base, **kwargs):
    # TODO Other types of sequences?
    return base("array", elt_dist=self.subtype.distribution(base, **kwargs),
                **kwargs)


class ExpressionType(VentureType):
  """A Venture expression is either a Venture self-evaluating object
(bool, number, integer, atom), or a Venture symbol, or a Venture array of
Venture Expressions.  Note: I adopt the convention that, to
distinguish them from numbers, Venture Atoms will be represented in
Python as VentureAtom objects for purposes of this type.

Note 2: Consumers of expressions should also be able to consume lists
of expressions, but the Python-side representation of expressions does
not distinguish the representation of lists and arrays.  So
round-tripping from Venture to Python and back will not be the
identity function, but should still be idempotent.

Note 3: The same discussion applies to other nice types like
VentureSPRecords.

In Haskell type notation:

data Expression = Bool | Number | Integer | Atom | Symbol | Array Expression
"""
  def __init__(self, name=None):
    self._name = name

  def asVentureValue(self, thing):
    if isinstance(thing, bool) or isinstance(thing, np.bool_):
      return vv.VentureBool(thing)
    if isinstance(thing, int):
      return vv.VentureInteger(thing)
    if isinstance(thing, numbers.Number):
      return vv.VentureNumber(thing)
    if isinstance(thing, vv.VentureAtom):
      return thing
    if isinstance(thing, str):
      return vv.VentureSymbol(thing)
    if hasattr(thing, "__getitem__"): # Already not a string
      return vv.VentureArray([self.asVentureValue(val) for val in thing])
    if isinstance(thing, vv.VentureValue):
      return thing
    else:
      raise Exception("Cannot convert Python object %r to a Venture " \
                      "Expression" % thing)

  def asPython(self, thing):
    if isinstance(thing, vv.VentureBool):
      return thing.getBool()
    if isinstance(thing, vv.VentureInteger):
      return thing.getInteger()
    if isinstance(thing, vv.VentureNumber):
      return thing.getNumber()
    if isinstance(thing, vv.VentureAtom):
      return thing # Atoms are valid elements of expressions
    if isinstance(thing, vv.VentureSymbol):
      return thing.getSymbol()
    if thing.isValidCompoundForm():
      # Leave quoted data as they are, on the grounds that (quote
      # <thing>) should evaluate to exactly that <thing>, even if
      # constructed programmatically from a <thing> that does not
      # normally appear in expressions.
      if thing.size() == 2 \
         and thing.lookup(vv.VentureNumber(0)) == vv.VentureSymbol("quote"):
        return ["quote", thing.lookup(vv.VentureNumber(1))]
      else:
        return thing.asPythonList(self)
    # Most other things are represented as themselves.
    return thing

  def name(self): return self._name or "<exp>"

class HomogeneousDictType(VentureType):
  """Type objects for homogeneous dicts.  Right now, the homogeneity
  is not captured in the implementation, in that on the Venture side
  such data is still stored as heterogenous Venture dicts.  This type
  does, however, encapsulate the necessary wrapping and unwrapping."""
  def __init__(self, keytype, valtype, name = None):
    assert isinstance(keytype, VentureType)
    assert isinstance(valtype, VentureType)
    self.keytype = keytype
    self.valtype = valtype
    self._name = name
  def asVentureValue(self, thing):
    return vv.VentureDict(dict([(self.keytype.asVentureValue(key),
                                 self.valtype.asVentureValue(val))
                                for (key, val) in thing.iteritems()]))
  def asPython(self, vthing):
    return dict([(self.keytype.asPython(key),
                  self.valtype.asPython(val))
                 for (key, val) in vthing.getDict().iteritems()])
  def __contains__(self, vthing):
    return isinstance(vthing, vv.VentureDict) \
      and all([key in self.keytype and val in self.valtype
               for (key,val) in vthing.getDict().iteritems()])
  def __eq__(self, other):
    return type(self) == type(other) \
      and self.keytype == other.keytype and self.valtype == other.valtype
  def name(self):
    return self._name or "<dict %s %s>" % \
      (self.keytype.name(), self.valtype.name())
  def distribution(self, base, **kwargs):
    # TODO Is this splitting what I want?
    return base("dict", key_dist=self.keytype.distribution(base, **kwargs),
                val_dist=self.valtype.distribution(base, **kwargs), **kwargs)

class HomogeneousMappingType(VentureType):
  """Type objects for all Venture mappings.  Dicts are the only fully
  generic mappings, but Venture also treats arrays and lists as
  mappings from integers to values, and environments as mappings from
  symbols to values.  This type is purely advisory and does not do any
  conversion."""
  def __init__(self, keytype, valtype, name = None):
    assert isinstance(keytype, VentureType)
    assert isinstance(valtype, VentureType)
    self.keytype = keytype
    self.valtype = valtype
    self._name = name
  def asVentureValue(self, thing):
    return thing
  def asPython(self, vthing):
    if not isinstance(vthing, (vv.VentureArray, vv.VentureArrayUnboxed,
                               vv.VentureNil, vv.VenturePair,
                               vv.VentureMatrix, vv.VentureDict,
                               vv.VentureSimplex)):
      raise vv.VentureTypeError(str(vthing) + " is not a HomogeneousMappingType!")
    return vthing
  def name(self):
    return self._name or "<mapping %s %s>" % \
      (self.keytype.name(), self.valtype.name())
  def distribution(self, base, **kwargs):
    # TODO Is this splitting what I want?
    return base("mapping", key_dist=self.keytype.distribution(base, **kwargs),
                val_dist=self.valtype.distribution(base, **kwargs), **kwargs)

class RequestType(VentureType):
  """A type object for Venture's Requests.  Requests are not Venture
  values in the strict sense, and reflection is not permitted on them.
  This type exists to permit requester PSPs to be wrapped in the
  TypedPSP wrapper."""
  def __init__(self, name="<request>"):
    # Accept a name to report in the documentation because the
    # synthesizer is not clever enough to properly compose
    # descriptions of SPs from descriptions of their PSPs.
    self._name = name
  def asVentureValue(self, thing):
    assert isinstance(thing, req.Request)
    return thing
  def asPython(self, thing):
    assert isinstance(thing, req.Request)
    return thing
  def name(self): return self._name

class ZeroType(VentureType):
  """A type object representing elements of the zero-dimensional vector
space.  This is needed only to serve as the gradient type of discrete
types like BoolType."""
  def __init__(self, name=None):
    self._name = name
  def asVentureValue(self, thing):
    assert thing == 0
    return thing
  def asPython(self, thing):
    assert thing == 0
    return thing
  def name(self): return self._name or "<zero>"

## Smart constructors
## The idea is to enable a (relatively) convenient embedded DSL for specifying Venture types.

# Many of the type definitions are metaprogrammed
# pylint:disable=undefined-variable
Object = AnyType()
Number = NumberType()
Int = IntegerType()
Atom = AtomType()
Bool = BoolType()
Symbol = SymbolType()
String = StringType()
Blob = ForeignBlobType()
Probability = ProbabilityType()
Count = CountType()
Positive = PositiveType()
Nil = NilType()
Zero = ZeroType()

def Array(subtype=None):
  if subtype is None:
    return ArrayType()
  else:
    return HomogeneousArrayType(subtype)

Simplex = SimplexType()
Matrix = MatrixType()
MatrixSym = SymmetricMatrixType()

def Pair(first, second):
  return PairType(first, second)

def List(subtype=None):
  if subtype is None:
    return ListType()
  else:
    return HomogeneousListType(subtype)

def Dict(keytype = None, valtype = None):
  if keytype is None and valtype is None:
    return DictType()
  elif keytype is not None and valtype is not None:
    return HomogeneousDictType(keytype, valtype)
  else:
    raise Exception("Dict must be either fully homogeneous or fully " \
                    "heterogeneous, got %s, %s" % (keytype, valtype))

def UArray(subtype):
  return ArrayUnboxedType(subtype)

def Seq(subtype):
  return HomogeneousSequenceType(subtype)

Exp = ExpressionType()
Request = RequestType()

def Mapping(keytype, valtype):
  return HomogeneousMappingType(keytype, valtype)
