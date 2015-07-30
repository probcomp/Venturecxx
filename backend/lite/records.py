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

from numbers import Number

import value as vv
import types as t
from exception import VentureTypeError
import builtin

from sp_registry import registerBuiltinSP

class RecordType(t.VentureType):
  def __init__(self, tag, name_extra=None):
    self.tag = tag
    self.name_extra = name_extra

  def asVentureValue(self, thing):
    assert isinstance(thing, VentureRecord) and thing.tag == self.tag
    return thing

  def asPython(self, vthing):
    # TODO Consider automatic unpacking of records?
    return vthing

  def __contains__(self, vthing):
    return isinstance(vthing, VentureRecord) and vthing.tag == self.tag

  def name(self):
    if self.name_extra is not None:
      return "<" + self.tag + " " + self.name_extra + ">"
    else:
      return "<" + self.tag + ">"

class VentureRecord(vv.VentureValue):
  def __init__(self, tag, fields):
    self.tag = tag
    self.fields = fields

  def asStackDict(self, _trace=None):
    return {"type":"record", "tag":self.tag, "fields":self.fields}

  @staticmethod
  def fromStackDict(thing):
    return VentureRecord(thing["tag"], [vv.VentureValue.fromStackDict(val) for val in thing["fields"]])

  def compareSameType(self, other):
    if self.tag == other.tag:
      return vv.lexicographicBoxedCompare(self.fields, other.fields)
    else:
      return self.tag < other.tag

  def __hash__(self):
    return vv.sequenceHash([vv.VentureSymbol(self.tag)] + self.fields)

  def __add__(self, other):
    if other == 0:
      return self
    elif self.tag == other.tag:
      return VentureRecord(self.tag, [x + y for (x,y) in zip(self.fields, other.fields)])
    else:
      raise VentureTypeError("Cannot add objects of incompatible types %s, %s" % (self, other))

  def __radd__(self, other):
    if other == 0:
      return self
    elif self.tag == other.tag:
      return VentureRecord(self.tag, [y + x for (x,y) in zip(self.fields, other.fields)])
    else:
      raise VentureTypeError("Cannot add objects of incompatible types %s, %s" % (other, self))

  def __neg__(self):
    return VentureRecord(self.tag, [-x for x in self.fields])

  def __sub__(self, other):
    if other == 0:
      return self
    elif self.tag == other.tag:
      return VentureRecord(self.tag, [x - y for (x,y) in zip(self.fields, other.fields)])
    else:
      raise VentureTypeError("Cannot subtract objects of incompatible types %s, %s" % (self, other))

  def __mul__(self, other):
    # Assume other is a scalar
    assert isinstance(other, Number)
    return VentureRecord(self.tag, [x * other for x in self.fields])

  def __rmul__(self, other):
    # Assume other is a scalar
    assert isinstance(other, Number)
    return VentureRecord(self.tag, [other * x for x in self.fields])

  def dot(self, other):
    if self.tag == other.tag:
      return sum([vv.vv_dot_product(x, y) for (x,y) in zip(self.fields, other.fields)])
    else:
      raise VentureTypeError("Cannot dot objects of incompatible types %s, %s" % (self, other))

  def map_real(self, f):
    return VentureRecord(self.tag, [x.map_real(f) for x in self.fields])

def record(tag, arity):
  typ = RecordType(tag)
  tester = builtin.type_test(typ)
  constructor = builtin.deterministic_typed(lambda *fields: VentureRecord(tag, fields),
                                            [t.AnyType()] * arity, typ,
                                            descr="%s" + " constructs a %s record" % tag)
  def accessor_func(r, i):
    if r in typ:
      return r.fields[i]
    else:
      raise VentureTypeError("Accessor for field %s expected record of type %s but got %s" % (i, tag, r))
  def accessor(i):
    return builtin.deterministic_typed(lambda r: accessor_func(r, i),
                                       [typ], t.AnyType(),
                                       descr="%s" + " extracts the %s field of a %s record" % (i, tag))

  return (tester, constructor, [accessor(i) for i in range(arity)])

def register_record(name, *fields):
  (tester, constructor, accessors) = record(name, len(fields))
  registerBuiltinSP(name, constructor)
  registerBuiltinSP("is_" + name, tester)
  for (f, a) in zip(fields, accessors):
    registerBuiltinSP(f, a)

register_record("inference_action", "action_func")
