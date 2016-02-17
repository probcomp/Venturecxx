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

import numpy as np

from venture.lite.sp import SPType
from venture.lite.sp_help import deterministic_psp
from venture.lite.sp_help import dispatching_psp
from venture.lite.sp_help import no_request
from venture.lite.sp_registry import registerBuiltinSP
import venture.lite.types as t

generic_biplex = dispatching_psp(
  [SPType([t.BoolType(), t.AnyType(), t.AnyType()], t.AnyType()),
   SPType([t.ArrayUnboxedType(t.NumberType()), t.ArrayUnboxedType(t.NumberType()), t.ArrayUnboxedType(t.NumberType())], t.ArrayUnboxedType(t.NumberType()))],
  [deterministic_psp(lambda p, c, a: c if p else a,
                     sim_grad=lambda args, direction: [0, direction, 0] if args[0] else [0, 0, direction],
                     descr="biplex returns either its second or third argument, depending on the first."),
   deterministic_psp(np.where,
                     # TODO sim_grad
                     descr="vector-wise biplex")])

registerBuiltinSP("biplex", no_request(generic_biplex))
