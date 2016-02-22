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

"""(Deterministic) vector operation SPs"""

from numbers import Number

import numpy as np

from venture.lite.exception import VentureValueError
from venture.lite.sp_help import deterministic_typed
from venture.lite.sp_help import type_test
from venture.lite.sp_registry import registerBuiltinSP
import venture.lite.types as t

registerBuiltinSP("array",
  deterministic_typed(lambda *args: np.array(args),
    [t.AnyType()], t.ArrayType(), variadic=True,
    sim_grad=lambda args, direction: direction.getArray(),
    descr="array returns an array initialized with its arguments"))

registerBuiltinSP("vector",
  deterministic_typed(lambda *args: np.array(args),
    [t.NumberType()], t.ArrayUnboxedType(t.NumberType()), variadic=True,
    sim_grad=lambda args, direction: direction.getArray(),
    descr="vector returns an unboxed numeric array initialized with its arguments"))

registerBuiltinSP("is_array", type_test(t.ArrayType()))
registerBuiltinSP("is_vector", type_test(t.ArrayUnboxedType(t.NumberType())))

registerBuiltinSP("to_array",
  deterministic_typed(lambda seq: seq.getArray(),
    [t.HomogeneousSequenceType(t.AnyType())], t.ArrayType(),
    descr="to_array converts its argument sequence to an array"))

registerBuiltinSP("to_vector",
  deterministic_typed(lambda seq: np.array(seq.getArray(t.NumberType())),
    [t.HomogeneousSequenceType(t.NumberType())],
    t.ArrayUnboxedType(t.NumberType()),
    descr="to_vector converts its argument sequence to a vector"))

registerBuiltinSP("matrix",
  deterministic_typed(np.array,
    [t.HomogeneousListType(t.HomogeneousListType(t.NumberType()))],
    t.MatrixType(),
    descr="matrix returns a matrix formed from the given list of rows.  " \
          "It is an error if the given list is not rectangular."))

registerBuiltinSP("is_matrix", type_test(t.MatrixType()))

registerBuiltinSP("simplex",
  deterministic_typed(lambda *nums: np.array(nums),
    [t.ProbabilityType()], t.SimplexType(), variadic=True,
    descr="simplex returns the simplex point given by its argument coordinates."))

registerBuiltinSP("is_simplex", type_test(t.SimplexType()))

registerBuiltinSP("arange",
  deterministic_typed(np.arange,
    [t.IntegerType(), t.IntegerType()],
    t.ArrayUnboxedType(t.IntegerType()),
    min_req_args=1,
    descr="%s([start], stop) returns an array of n consecutive integers " \
          "from start (inclusive) up to stop (exclusive)."))

registerBuiltinSP("fill",
  deterministic_typed(np.full,
    [t.IntegerType(), t.NumberType()],
    t.ArrayUnboxedType(t.NumberType()),
    descr="%s(n, x) returns an array with the number x repeated n times"))

registerBuiltinSP("linspace",
  deterministic_typed(np.linspace,
    [t.NumberType(), t.NumberType(), t.CountType()],
    t.ArrayUnboxedType(t.NumberType()),
    descr="%s(start, stop, n) returns an array of n evenly spaced numbers " \
          "over the interval [start, stop]."))

registerBuiltinSP("id_matrix",
  deterministic_typed(np.identity, [t.CountType()], t.MatrixType(),
    descr="%s(n) returns an identity matrix of dimension n."))

registerBuiltinSP("diag_matrix",
  deterministic_typed(np.diag,
    [t.ArrayUnboxedType(t.NumberType())],
    t.MatrixType(),
    descr="%s(v) returns a diagonal array whose diagonal is v."))

registerBuiltinSP("ravel",
  deterministic_typed(np.ravel,
    [t.MatrixType()],
    t.ArrayUnboxedType(t.NumberType()),
    descr="%s(m) returns a 1-D array containing the elements of the matrix m."))

registerBuiltinSP("transpose",
  deterministic_typed(np.transpose,
    [t.MatrixType()],
    t.MatrixType(),
    descr="%s(m) returns the transpose of the matrix m."))

registerBuiltinSP("vector_add",
  deterministic_typed(np.add,
    [t.ArrayUnboxedType(t.NumberType()), t.ArrayUnboxedType(t.NumberType())],
    t.ArrayUnboxedType(t.NumberType()),
    descr="%s(x, y) returns the sum of vectors x and y."))

registerBuiltinSP("matrix_add",
  deterministic_typed(np.add,
    [t.MatrixType(), t.MatrixType()],
    t.MatrixType(),
    descr="%s(x, y) returns the sum of matrices x and y."))

registerBuiltinSP("scale_vector",
  deterministic_typed(np.multiply,
    [t.NumberType(), t.ArrayUnboxedType(t.NumberType())],
    t.ArrayUnboxedType(t.NumberType()),
    descr="%s(x, y) returns the product of scalar x and vector y."))

registerBuiltinSP("scale_matrix",
  deterministic_typed(np.multiply,
    [t.NumberType(), t.MatrixType()],
    t.MatrixType(),
    descr="%s(x, y) returns the product of scalar x and matrix y."))

def vector_dot(v1, v2):
  candidate = np.dot(v1, v2)
  if isinstance(candidate, Number):  # Numpy! WTF?
    return candidate
  else:
    return 0

def grad_vector_dot(args, direction):
  gradient_type = t.HomogeneousArrayType(t.NumberType())
  untyped = [args[1], args[0]]
  unscaled = [gradient_type.asVentureValue(x) for x in untyped]
  return [direction.getNumber() * x for x in unscaled]

registerBuiltinSP("vector_dot",
  deterministic_typed(vector_dot,
    [t.ArrayUnboxedType(t.NumberType()), t.ArrayUnboxedType(t.NumberType())],
    t.NumberType(),
    sim_grad=grad_vector_dot,
    descr="%s(x, y) returns the dot product of vectors x and y."))

registerBuiltinSP("matrix_mul",
  deterministic_typed(np.dot,
    [t.MatrixType(), t.MatrixType()],
    t.MatrixType(),
    descr="%s(x, y) returns the product of matrices x and y."))

registerBuiltinSP("matrix_times_vector",
  deterministic_typed(np.dot,
    [t.MatrixType(), t.ArrayUnboxedType(t.NumberType())],
    t.ArrayUnboxedType(t.NumberType()),
    descr="%s(M, v) returns the matrix-vector product Mv."))

registerBuiltinSP("vector_times_matrix",
  deterministic_typed(np.dot,
    [t.ArrayUnboxedType(t.NumberType()), t.MatrixType()],
    t.ArrayUnboxedType(t.NumberType()),
    descr="%s(v, M) returns the vector-matrix product vM."))

def catches_linalg_error(f, *args, **kwargs):
  def try_f(*args, **kwargs):
    try:
      return f(*args, **kwargs)
    except np.linalg.LinAlgError as e: raise VentureValueError(e)
  return try_f

registerBuiltinSP("matrix_inverse",
  deterministic_typed(catches_linalg_error(np.linalg.inv),
    [t.MatrixType()],
    t.MatrixType(),
    descr="%s(M) returns the (multiplicative) inverse of the matrix M."))

registerBuiltinSP("matrix_solve",
  deterministic_typed(catches_linalg_error(np.linalg.solve),
    [t.MatrixType(), t.MatrixType()],
    t.MatrixType(),
    descr="%s(A, B) returns the solution to the matrix equation AX = B."))
