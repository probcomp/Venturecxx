# Copyright (c) 2013, 2014, 2015 MIT Probabilistic Computing Project.
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

"""(Deterministic) basic programming SPs"""

from venture.lite.exception import VentureValueError
from venture.lite.sp import SPType
from venture.lite.sp_help import binaryPred
from venture.lite.sp_help import deterministic_typed
from venture.lite.sp_help import type_test
from venture.lite.sp_registry import registerBuiltinSP
from venture.lite.utils import raise_
import venture.lite.types as t
import venture.lite.value as v

registerBuiltinSP("eq", binaryPred(lambda x,y: x.compare(y) == 0,
    descr="eq compares its two arguments for equality"))

registerBuiltinSP("neq", binaryPred(lambda x,y: x.compare(y) != 0,
    descr="neq checkes whether its arguments are not equal"))

registerBuiltinSP("gt", binaryPred(lambda x,y: x.compare(y) >  0,
    descr="gt returns true if its first argument compares greater " \
          "than its second"))

registerBuiltinSP("gte", binaryPred(lambda x,y: x.compare(y) >= 0,
    descr="gte returns true if its first argument compares greater " \
          "than or equal to its second"))

registerBuiltinSP("lt", binaryPred(lambda x,y: x.compare(y) <  0,
    descr="lt returns true if its first argument compares less than its " \
          "second"))

registerBuiltinSP("lte", binaryPred(lambda x,y: x.compare(y) <= 0,
    descr="lte returns true if its first argument compares less than or " \
          "equal to its second"))

# If you are wondering about the type signature, this function
# bootstraps the implicit coersion to numbers into an explicit one.
registerBuiltinSP("real", deterministic_typed(lambda x:x,
    [t.NumberType()], t.NumberType(),
    descr="real explicitly coerces its argument to a number"))

registerBuiltinSP("atom", deterministic_typed(lambda x:x,
    [t.IntegerType()], t.AtomType(),
    descr="atom returns the identity of its argument integer as an atom"))

registerBuiltinSP("atom_index", deterministic_typed(lambda x:x,
    [t.AtomType()], t.IntegerType(),
    descr="atom_index returns the identity of its argument atom as an integer"))

registerBuiltinSP("integer", deterministic_typed(int,
    [t.NumberType()], t.IntegerType(),
    descr="integer returns the floor of its argument number as an integer"))

registerBuiltinSP("probability", deterministic_typed(lambda x:x,
    [t.ProbabilityType()], t.ProbabilityType(),
    descr="probability converts its argument to a probability " \
          "(in direct space)"))

registerBuiltinSP("not", deterministic_typed(lambda x: not x,
    [t.BoolType()], t.BoolType(),
    descr="not returns the logical negation of its argument"))
registerBuiltinSP("xor", deterministic_typed(lambda x, y: x != y,
    [t.BoolType(), t.BoolType()], t.BoolType(),
    descr="xor(x,y) returns true if exactly one of x and y is true"))

registerBuiltinSP("all_p", deterministic_typed(all,
    [t.HomogeneousListType(t.BoolType())], t.BoolType(),
    descr="all returns true if all of the elements in the input are true"))

registerBuiltinSP("any_p", deterministic_typed(any,
    [t.HomogeneousListType(t.BoolType())], t.BoolType(),
    descr="any returns true if any of the elements in the input are true"))

registerBuiltinSP("is_number", type_test(t.NumberType()))
registerBuiltinSP("is_integer", type_test(t.IntegerType()))
registerBuiltinSP("is_probability", type_test(t.ProbabilityType()))
registerBuiltinSP("is_atom", type_test(t.AtomType()))
registerBuiltinSP("is_boolean", type_test(t.BoolType()))
registerBuiltinSP("is_symbol", type_test(t.SymbolType()))
registerBuiltinSP("is_procedure", type_test(SPType([t.AnyType()], t.AnyType(),
                                                   variadic=True)))

def grad_list(args, direction):
  if direction == 0:
    return [0 for _ in args]
  else:
    (list_, tail) = direction.asPossiblyImproperList()
    assert tail is None or tail == 0
    tails = [0 for _ in range(len(args) - len(list_))]
    return list_ + tails

registerBuiltinSP("list", deterministic_typed(lambda *args: args,
    [t.AnyType()], t.ListType(), variadic=True, sim_grad=grad_list,
    descr="list returns the list of its arguments"))

registerBuiltinSP("pair", deterministic_typed(lambda a,d: (a,d),
    [t.AnyType(), t.AnyType()], t.PairType(),
    descr="pair returns the pair whose first component is the first " \
          "argument and whose second component is the second argument"))

registerBuiltinSP("is_pair", type_test(t.PairType()))

registerBuiltinSP("first", deterministic_typed(lambda p: p[0],
    [t.PairType()], t.AnyType(),
    sim_grad=lambda args, direction: [v.VenturePair((direction, 0))],
    descr="first returns the first component of its argument pair"))

registerBuiltinSP("rest", deterministic_typed(lambda p: p[1],
    [t.PairType()], t.AnyType(),
    sim_grad=lambda args, direction: [v.VenturePair((0, direction))],
    descr="rest returns the second component of its argument pair"))

registerBuiltinSP("second", deterministic_typed(lambda p: p[1][0],
    [t.PairType(second_type=t.PairType())], t.AnyType(),
    sim_grad=lambda args, direction:
      [v.VenturePair((0, v.VenturePair((direction, 0))))],
    descr="second returns the first component of the second component " \
          "of its argument"))

registerBuiltinSP("to_list",
  deterministic_typed(lambda seq: seq.asPythonList(),
    [t.HomogeneousSequenceType(t.AnyType())],
    t.HomogeneousListType(t.AnyType()),
    descr="to_list converts its argument sequence to a list"))

registerBuiltinSP("zip", deterministic_typed(zip,
    [t.ListType()], t.HomogeneousListType(t.ListType()), variadic=True,
    descr="zip returns a list of lists, where the i-th nested list " \
          "contains the i-th element from each of the input arguments"))

def mk_dict(*entries):
  return dict([(e.lookup(v.VentureNumber(0)), e.lookup(v.VentureNumber(1)))
               for e in entries])

registerBuiltinSP("dict",
    deterministic_typed(mk_dict,
    [t.AnyType("2-tuple(k, v)")],
    t.HomogeneousDictType(t.AnyType("k"), t.AnyType("v")),
    descr="dict returns the dictionary mapping each of the given keys to their " \
          "respective given values.",
    variadic=True))
registerBuiltinSP("is_dict", type_test(t.DictType()))

registerBuiltinSP("to_dict",
  deterministic_typed(lambda entries: mk_dict(*entries),
    [t.HomogeneousListType(t.AnyType("2-tuple(k, v)"))],
     t.HomogeneousDictType(t.AnyType("k"), t.AnyType("v")),
     descr="to_dict returns the dictionary mapping each of the given keys to their " \
           "respective given values."))

registerBuiltinSP("keys",
  deterministic_typed(lambda d: d.keys(),
    [t.HomogeneousDictType(t.AnyType("k"), t.AnyType("v"))],
    t.HomogeneousListType(t.AnyType("k")),
    descr="keys returns a list of keys of the given dictionary."))

registerBuiltinSP("values",
  deterministic_typed(lambda d: d.values(),
    [t.HomogeneousDictType(t.AnyType("k"), t.AnyType("v"))],
    t.HomogeneousListType(t.AnyType("v")),
    descr="values returns a list of values of the given dictionary."))

registerBuiltinSP("lookup", deterministic_typed(lambda xs, x: xs.lookup(x),
    [t.HomogeneousMappingType(t.AnyType("k"), t.AnyType("v")), t.AnyType("k")],
    t.AnyType("v"),
    sim_grad=lambda args, direction:
      [args[0].lookup_grad(args[1], direction), 0],
    descr="lookup looks the given key up in the given mapping and returns " \
          "the result.  It is an error if the key is not in the mapping.  " \
          "Lists and arrays are viewed as mappings from indices to the " \
          "corresponding elements.  Environments are viewed as mappings " \
          "from symbols to their values."))

registerBuiltinSP("contains", deterministic_typed(lambda xs, x: xs.contains(x),
    [t.HomogeneousMappingType(t.AnyType("k"), t.AnyType("v")), t.AnyType("k")],
    t.BoolType(),
    descr="contains reports whether the given key appears in " \
          "the given mapping or not."))

registerBuiltinSP("size", deterministic_typed(lambda xs: xs.size(),
    [t.HomogeneousMappingType(t.AnyType("k"), t.AnyType("v"))],
    t.IntegerType(),
    descr="size returns the number of elements in the given collection " \
          "(lists and arrays work too)"))

registerBuiltinSP("is_empty", deterministic_typed(lambda xs: xs.size() == 0,
    [t.HomogeneousMappingType(t.AnyType("k"), t.AnyType("v"))],
    t.BoolType(),
    descr="is_empty returns whether the given collection is empty " \
          "(lists and arrays work too)"))

registerBuiltinSP("take", deterministic_typed(lambda ind, xs: xs.take(ind),
    [t.IntegerType(), t.HomogeneousSequenceType(t.AnyType("k"))],
    t.HomogeneousSequenceType(t.AnyType("k")),
    descr="take returns the requested number of elements from the " \
          "beginning of the given sequence, as another sequence of " \
          "the same type."))

def debug_print(label, value):
  print 'debug ' + label + ': ' + str(value)
  return value

registerBuiltinSP("debug", deterministic_typed(debug_print,
    [t.StringType(), t.AnyType("k")], t.AnyType("k"),
    descr = "Print the given value, labeled by a string. Return the value. " \
            "Intended for debugging or for monitoring execution."))

registerBuiltinSP("value_error",
  deterministic_typed(lambda s: raise_(VentureValueError(str(s))),
    [t.AnyType()], t.AnyType()))

def make_name(sym, index):
  return sym + "_" + str(int(index))

registerBuiltinSP("name", deterministic_typed(make_name,
    [t.SymbolType(), t.NumberType()], t.SymbolType(),
    descr = "Programmatically synthesize a variable name. " \
            "The name is determined by the given prefix and index."))
