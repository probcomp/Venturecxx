# Copyright (c) 2015 MIT Probabilistic Computing Project.
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

from value import *
from request import Request

### Venture Types

class VentureType(object):
  """Base class of all Venture types.  See the "Types" section of doc/type-system.md."""
  def asPythonNoneable(self, vthing):
    if vthing is None:
      return None
    else:
      return self.asPython(vthing) # Function will be added by inheritance pylint:disable=no-member
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
    assert isinstance(thing, VentureValue)
    return thing
  def asPython(self, thing):
    # TODO Make symbolic zeroes a venture value!
    assert isinstance(thing, VentureValue) or thing is 0
    return thing
  def __contains__(self, vthing): return isinstance(vthing, VentureValue)
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
  def asVentureValue(self, thing): return VentureNumber(thing)
  def asPython(self, vthing): return vthing.getNumber()
  def __contains__(self, vthing): return isinstance(vthing, VentureNumber)
  def name(self): return self._name or "<number>"

def standard_venture_type(typename, gradient_typename=None):
  if gradient_typename is None:
    gradient_typename = typename
  return """
class %sType(VentureType):
  def __init__(self, name=None):
    self._name = name
  def asVentureValue(self, thing): return Venture%s(thing)
  def asPython(self, vthing): return vthing.get%s()
  def __contains__(self, vthing): return isinstance(vthing, Venture%s)
  def name(self): return self._name or "<%s>"
  def gradient_type(self): return %sType()
""" % (typename, typename, typename, typename, typename.lower(), gradient_typename)

for typename in ["Integer", "Atom", "Bool", "Symbol", "ForeignBlob"]:
  # Exec is appropriate for metaprogramming, but indeed should not be used lightly.
  # pylint: disable=exec-used
  exec(standard_venture_type(typename, gradient_typename="Zero"))

for typename in ["Array", "Simplex", "Dict", "Matrix", "SymmetricMatrix"]:
  # Exec is appropriate for metaprogramming, but indeed should not be used lightly.
  # pylint: disable=exec-used
  exec(standard_venture_type(typename))

# Exec is appropriate for metaprogramming, but indeed should not be used lightly.
# pylint: disable=exec-used
exec(standard_venture_type("Probability", gradient_typename="Number"))

class CountType(VentureType):
  def __init__(self, name=None):
    self._name = name
  def asVentureValue(self, thing):
    assert 0 <= thing
    return VentureInteger(thing)
  def asPython(self, vthing):
    ans = vthing.getInteger()
    if 0 <= ans:
      return ans
    else:
      # TODO: Or what?  Clip to 0?
      raise VentureTypeError("Count is not positive %s" % self.number)
  def __contains__(self, vthing):
    return isinstance(vthing, VentureInteger) and 0 <= vthing.getInteger()
  def name(self): return self._name or "<count>"

class PositiveType(VentureType):
  def __init__(self, name=None):
    self._name = name
  def asVentureValue(self, thing):
    assert 0 < thing
    return VentureNumber(thing)
  def asPython(self, vthing):
    ans = vthing.getNumber()
    if 0 < ans:
      return ans
    else:
      # TODO: Or what?  Can't even clip to 0!
      raise VentureTypeError("Number is not positive %s" % ans)
  def __contains__(self, vthing):
    return isinstance(vthing, VentureNumber) and 0 < vthing.getNumber()
  def name(self): return self._name or "<positive>"
  def gradient_type(self): return NumberType()

class NilType(VentureType):
  def __init__(self, name=None):
    self._name = name
  def asVentureValue(self, _thing):
    # TODO Throw an error if not null-like?
    return VentureNil()
  def asPython(self, _vthing):
    # TODO Throw an error if not nil?
    return []
  def __contains__(self, vthing): return isinstance(vthing, VentureNil)
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
    return VenturePair((self.first_type.asVentureValue(f), self.second_type.asVentureValue(r)))
  def asPython(self, vthing):
    (vf, vr) = vthing.getPair()
    return (self.first_type.asPython(vf), self.second_type.asPython(vr))
  def __contains__(self, vthing): return isinstance(vthing, VenturePair)
  def name(self):
    if self._name is not None:
      return self._name
    if self.first_type is None and self.second_type is None:
      return "<pair>"
    first_name = self.first_type.name() if self.first_type else "<object>"
    second_name = self.second_type.name() if self.second_type else "<object>"
    return "<pair %s %s>" % (first_name, second_name)
  def distribution(self, base, **kwargs):
    first_dist = self.first_type.distribution(base, **kwargs) if self.first_type else None
    second_dist = self.second_type.distribution(base, **kwargs) if self.second_type else None
    return base("pair", first_dist=first_dist, second_dist=second_dist, **kwargs)

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
    return pythonListToVentureList(thing)
  def asPython(self, thing):
    return thing.asPythonList()
  def __contains__(self, vthing):
    return isinstance(vthing, VentureNil) or (isinstance(vthing, VenturePair) and vthing.rest in self)
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
    return pythonListToVentureList([self.subtype.asVentureValue(t) for t in thing])
  def asPython(self, vthing):
    return vthing.asPythonList(self.subtype)
  def __contains__(self, vthing):
    return vthing in ListType() and all([val in self.subtype for val in vthing.asPythonList()])
  def __eq__(self, other):
    return type(self) == type(other) and self.subtype == other.subtype
  def name(self): return self._name or "<list %s>" % self.subtype.name()
  def distribution(self, base, **kwargs):
    # TODO Is this splitting what I want?
    return base("list", elt_dist=self.subtype.distribution(base, **kwargs), **kwargs)

class HomogeneousArrayType(VentureType):
  """Type objects for homogeneous arrays.  Right now, the homogeneity
  is not captured in the implementation, in that on the Venture side
  such data is still stored as heterogenous Venture arrays.  This type
  does, however, encapsulate the necessary wrapping and unwrapping."""
  def __init__(self, subtype, name = None):
    assert isinstance(subtype, VentureType)
    self.subtype = subtype
    self._name = name
  def asVentureValue(self, thing):
    return VentureArray([self.subtype.asVentureValue(val) for val in thing])
  def asPython(self, vthing):
    return vthing.getArray(self.subtype)
  def __contains__(self, vthing):
    return isinstance(vthing, VentureArray) and all([val in self.subtype for val in vthing.getArray()])
  def __eq__(self, other):
    return type(self) == type(other) and self.subtype == other.subtype
  def name(self): return self._name or "<array %s>" % self.subtype.name()
  def distribution(self, base, **kwargs):
    # TODO Is this splitting what I want?
    return base("array", elt_dist=self.subtype.distribution(base, **kwargs), **kwargs)

class ArrayUnboxedType(VentureType):
  """Type objects for arrays of unboxed values.  Perforce homogeneous."""
  def __init__(self, subtype, name = None):
    assert isinstance(subtype, VentureType)
    self.subtype = subtype
    self._name = name
  def asVentureValue(self, thing):
    return VentureArrayUnboxed(thing, self.subtype)
  def asPython(self, vthing):
    return vthing.getArray(self.subtype)
  def __contains__(self, vthing):
    # TODO Need a more general element type compatibility check
    return isinstance(vthing, VentureArrayUnboxed) and vthing.elt_type == self.subtype
  def __eq__(self, other):
    return type(self) == type(other) and self.subtype == other.subtype
  def name(self): return self._name or "<array %s>" % self.subtype.name()
  def distribution(self, base, **kwargs):
    return base("array_unboxed", elt_type=self.subtype, **kwargs)

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
    return (isinstance(vthing, VentureArray) or isinstance(vthing, VentureSimplex) or isinstance(vthing, VentureArrayUnboxed) or vthing in ListType()) and all([val in self.subtype for val in vthing.getArray()])
  def __eq__(self, other):
    return type(self) == type(other) and self.subtype == other.subtype
  def name(self): return self._name or "<sequence %s>" % self.subtype.name()
  def distribution(self, base, **kwargs):
    # TODO Other types of sequences?
    return base("array", elt_dist=self.subtype.distribution(base, **kwargs), **kwargs)


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
      return VentureBool(thing)
    if isinstance(thing, int):
      return VentureInteger(thing)
    if isinstance(thing, Number):
      return VentureNumber(thing)
    if isinstance(thing, VentureAtom):
      return thing
    if isinstance(thing, str):
      return VentureSymbol(thing)
    if hasattr(thing, "__getitem__"): # Already not a string
      return VentureArray([self.asVentureValue(val) for val in thing])
    if isinstance(thing, VentureValue):
      return thing
    else:
      raise Exception("Cannot convert Python object %r to a Venture Expression" % thing)

  def asPython(self, thing):
    if isinstance(thing, VentureBool):
      return thing.getBool()
    if isinstance(thing, VentureInteger):
      return thing.getInteger()
    if isinstance(thing, VentureNumber):
      return thing.getNumber()
    if isinstance(thing, VentureAtom):
      return thing # Atoms are valid elements of expressions
    if isinstance(thing, VentureSymbol):
      return thing.getSymbol()
    if thing.isValidCompoundForm():
      # Leave quoted data as they are, on the grounds that (quote
      # <thing>) should evaluate to exactly that <thing>, even if
      # constructed programmatically from a <thing> that does not
      # normally appear in expressions.
      if thing.size() == 2 and thing.lookup(VentureNumber(0)) == VentureSymbol("quote"):
        return ["quote", thing.lookup(VentureNumber(1))]
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
    return VentureDict(dict([(self.keytype.asVentureValue(key), self.valtype.asVentureValue(val)) for (key, val) in thing.iteritems()]))
  def asPython(self, vthing):
    return dict([(self.keytype.asPython(key), self.valtype.asPython(val)) for (key, val) in vthing.getDict().iteritems()])
  def __contains__(self, vthing):
    return isinstance(vthing, VentureDict) and all([key in self.keytype and val in self.valtype for (key,val) in vthing.getDict().iteritems()])
  def __eq__(self, other):
    return type(self) == type(other) and self.keytype == other.keytype and self.valtype == other.valtype
  def name(self): return self._name or "<dict %s %s>" % (self.keytype.name(), self.valtype.name())
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
    if not isinstance(vthing, (VentureArray, VentureArrayUnboxed, VentureNil, VenturePair, VentureMatrix, VentureDict, VentureSimplex)):
      raise VentureTypeError(str(vthing) + " is not a HomogeneousMappingType!")
    return vthing
  def name(self): return self._name or "<mapping %s %s>" % (self.keytype.name(), self.valtype.name())
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
    assert isinstance(thing, Request)
    return thing
  def asPython(self, thing):
    assert isinstance(thing, Request)
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
