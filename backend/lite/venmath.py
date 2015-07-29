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

"""(Deterministic) Math SPs"""

import numpy as np
from sp import SPType
import value as v
import types as t
from sp_registry import registerBuiltinSP
from sp_help import dispatching_psp, deterministic_psp, no_request, binaryNum

from utils import raise_
from exception import VentureValueError

def vvsum(venture_array):
  # TODO Why do the directions come in and out as Venture Values
  # instead of being unpacked by f_type.gradient_type()?
  return v.VentureNumber(sum(venture_array.getArray(t.NumberType())))

generic_add = dispatching_psp(
  [SPType([t.NumberType()], t.NumberType(), variadic=True),
   SPType([t.ArrayUnboxedType(t.NumberType()), t.NumberType()],
          t.ArrayUnboxedType(t.NumberType())),
   SPType([t.NumberType(), t.ArrayUnboxedType(t.NumberType())],
          t.ArrayUnboxedType(t.NumberType())),
   SPType([t.ArrayUnboxedType(t.NumberType())], t.ArrayUnboxedType(t.NumberType()),
          variadic=True)],
  [deterministic_psp(lambda *args: sum(args),
                     sim_grad=lambda args, direction: [direction for _ in args],
                     descr="add returns the sum of all its arguments"),
   deterministic_psp(np.add, sim_grad=lambda args, direction: [direction, vvsum(direction)]),
   deterministic_psp(np.add, sim_grad=lambda args, direction: [vvsum(direction), direction]),
   deterministic_psp(lambda *args: np.sum(args, axis=0),
                     sim_grad=lambda args, direction: [direction for _ in args],
                     descr="add returns the sum of all its arguments")])

registerBuiltinSP("add", no_request(generic_add))

registerBuiltinSP("sub",
                  binaryNum(lambda x,y: x - y,
                            sim_grad=lambda args, direction: [direction, -direction],
                            descr="sub returns the difference between its first and second arguments"))

def grad_times(args, direction):
  assert len(args) == 2, "Gradient only available for binary multiply"
  return [direction*args[1], direction*args[0]]

generic_times = dispatching_psp(
  [SPType([t.NumberType()], t.NumberType(), variadic=True),
   SPType([t.NumberType(), t.ArrayUnboxedType(t.NumberType())],
          t.ArrayUnboxedType(t.NumberType())),
   SPType([t.ArrayUnboxedType(t.NumberType()), t.NumberType()],
          t.ArrayUnboxedType(t.NumberType()))],
  [deterministic_psp(lambda *args: reduce(lambda x,y: x * y,args,1),
                     sim_grad=grad_times,
                     descr="mul returns the product of all its arguments"),
   deterministic_psp(np.multiply,
                     sim_grad=lambda args, direction: [ v.VentureNumber(v.vv_dot_product(v.VentureArrayUnboxed(args[1], t.NumberType()), direction)), direction * args[0] ],
                     descr="scalar times vector"),
   deterministic_psp(np.multiply,
                     sim_grad=lambda args, direction: [ direction * args[1], v.VentureNumber(v.vv_dot_product(v.VentureArrayUnboxed(args[0], t.NumberType()), direction)) ],
                     descr="vector times scalar")])

registerBuiltinSP("mul", no_request(generic_times))

def grad_div(args, direction):
  return [direction * (1 / args[1]), direction * (- args[0] / (args[1] * args[1]))]

registerBuiltinSP("div",
                  binaryNum(lambda x,y: x / y,
                            sim_grad=grad_div,
                            descr="div returns the ratio of its first argument to its second") )

registerBuiltinSP("int_div",
                  binaryNum(lambda x,y: raise_(VentureValueError("division by zero")) if int(y) == 0 else int(x) // int(y),
                            descr="div returns the integer quotient of its first argument by its second"))

registerBuiltinSP("int_mod",
                  binaryNum(lambda x,y: raise_(VentureValueError("modulo by zero")) if int(y) == 0 else int(x) % int(y),
                            descr="mod returns the modulus of its first argument by its second"))

registerBuiltinSP("min",
                  binaryNum(min, descr="min returns the minimum value of its arguments"))

