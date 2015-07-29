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
from numbers import Number

from sp import SP, SPType
from psp import TypedPSP

from sp_registry import registerBuiltinSP, builtInSPs, builtInSPsIter # Importing for re-export pylint:disable=unused-import

import value as v
import types as t
import env
from utils import raise_
from exception import VentureValueError

from sp_help import *

# These modules actually define the PSPs.
import venmath
import basic_sps
import discrete
import dirichlet
import continuous
import csp
import crp
import function
import gp
import msp
import hmm
import conditionals
import scope
import eval_sps
import functional
import cmvn

# The types in the types module are generated programmatically, so
# pylint doesn't find out about them.
# pylint: disable=no-member

def builtInValues():
  return { "true" : v.VentureBool(True), "false" : v.VentureBool(False), "nil" : v.VentureNil() }

def debug_print(label, value):
  print 'debug ' + label + ': ' + str(value)
  return value

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

def catches_linalg_error(f, *args, **kwargs):
  def try_f(*args, **kwargs):
    try:
      return f(*args, **kwargs)
    except np.linalg.LinAlgError as e: raise VentureValueError(e)
  return try_f

generic_biplex = dispatching_psp(
  [SPType([t.BoolType(), t.AnyType(), t.AnyType()], t.AnyType()),
   SPType([t.ArrayUnboxedType(t.NumberType()), t.ArrayUnboxedType(t.NumberType()), t.ArrayUnboxedType(t.NumberType())], t.ArrayUnboxedType(t.NumberType()))],
  [deterministic_psp(lambda p, c, a: c if p else a,
                     sim_grad=lambda args, direction: [0, direction, 0] if args[0] else [0, 0, direction],
                     descr="biplex returns either its second or third argument, depending on the first."),
   deterministic_psp(np.where,
                     # TODO sim_grad
                     descr="vector-wise biplex")])

generic_normal = dispatching_psp(
  [SPType([t.NumberType(), t.NumberType()], t.NumberType()), # TODO Sigma is really non-zero, but negative is OK by scaling
   SPType([t.NumberType(), t.ArrayUnboxedType(t.NumberType())],
          t.ArrayUnboxedType(t.NumberType())),
   SPType([t.ArrayUnboxedType(t.NumberType()), t.NumberType()],
          t.ArrayUnboxedType(t.NumberType())),
   SPType([t.ArrayUnboxedType(t.NumberType()), t.ArrayUnboxedType(t.NumberType())],
          t.ArrayUnboxedType(t.NumberType()))],
  [continuous.NormalOutputPSP(), continuous.NormalsvOutputPSP(),
   continuous.NormalvsOutputPSP(), continuous.NormalvvOutputPSP()])



registerBuiltinSP("array", deterministic_typed(lambda *args: np.array(args),
                                               [t.AnyType()], t.ArrayType(), variadic=True,
                                               sim_grad=lambda args, direction: direction.getArray(),
                                               descr="array returns an array initialized with its arguments"))

registerBuiltinSP("vector", deterministic_typed(lambda *args: np.array(args),
                                                [t.NumberType()], t.ArrayUnboxedType(t.NumberType()), variadic=True,
                                                sim_grad=lambda args, direction: direction.getArray(),
                                                descr="vector returns an unboxed numeric array initialized with its arguments"))

registerBuiltinSP("is_array", type_test(t.ArrayType()))
registerBuiltinSP("is_vector", type_test(t.ArrayUnboxedType(t.NumberType())))

registerBuiltinSP("to_array", deterministic_typed(lambda seq: seq.getArray(),
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
                                      descr="matrix returns a matrix formed from the given list of rows.  It is an error if the given list is not rectangular."))
registerBuiltinSP("is_matrix", type_test(t.MatrixType()))
registerBuiltinSP("simplex", deterministic_typed(lambda *nums: np.array(nums),
                                                 [t.ProbabilityType()], t.SimplexType(), variadic=True,
                                                 descr="simplex returns the simplex point given by its argument coordinates."))
registerBuiltinSP("is_simplex", type_test(t.SimplexType()))

registerBuiltinSP("arange", deterministic_typed(np.arange,
                                                [t.IntegerType(), t.IntegerType()],
                                                t.ArrayUnboxedType(t.IntegerType()),
                                                min_req_args=1,
                                                descr="%s([start], stop) returns an array of n consecutive integers from start (inclusive) up to stop (exclusive)."))

registerBuiltinSP("fill", deterministic_typed(np.full,
                                              [t.IntegerType(), t.NumberType()],
                                              t.ArrayUnboxedType(t.NumberType()),
                                              descr="%s(n, x) returns an array with the number x repeated n times"))

registerBuiltinSP("linspace", deterministic_typed(np.linspace,
                                                  [t.NumberType(), t.NumberType(), t.CountType()],
                                                  t.ArrayUnboxedType(t.NumberType()),
                                                  descr="%s(start, stop, n) returns an array of n evenly spaced numbers over the interval [start, stop]."))

registerBuiltinSP("id_matrix", deterministic_typed(np.identity, [t.CountType()], t.MatrixType(),
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

registerBuiltinSP("debug",
                  deterministic_typed(debug_print, [t.SymbolType(), t.AnyType("k")], t.AnyType("k"),
                                      descr = "Print the given value, labeled by a Symbol. Return the value. Intended for debugging or for monitoring execution."))

registerBuiltinSP("apply", esr_output(TypedPSP(functional.ApplyRequestPSP(),
                                               SPType([SPType([t.AnyType("a")], t.AnyType("b"), variadic=True),
                                                       t.HomogeneousArrayType(t.AnyType("a"))],
                                                      t.RequestType("b")))))

registerBuiltinSP("fix", SP(TypedPSP(functional.FixRequestPSP(),
                                     SPType([t.HomogeneousArrayType(t.SymbolType()),
                                             t.HomogeneousArrayType(t.ExpressionType())],
                                            t.RequestType())),
                            TypedPSP(functional.FixOutputPSP(),
                                     SPType([t.HomogeneousArrayType(t.SymbolType()),
                                             t.HomogeneousArrayType(t.ExpressionType())],
                                            env.EnvironmentType()))))

registerBuiltinSP("mapv", SP(TypedPSP(functional.ArrayMapRequestPSP(),
                                      SPType([SPType([t.AnyType("a")], t.AnyType("b")),
                                              t.HomogeneousArrayType(t.AnyType("a"))],
                                             t.RequestType("<array b>"))),
                             functional.ESRArrayOutputPSP()))

registerBuiltinSP("imapv", SP(TypedPSP(functional.IndexedArrayMapRequestPSP(),
                                       SPType([SPType([t.AnyType("index"), t.AnyType("a")], t.AnyType("b")),
                                               t.HomogeneousArrayType(t.AnyType("a"))],
                                              t.RequestType("<array b>"))),
                              functional.ESRArrayOutputPSP()))

registerBuiltinSP("zip", deterministic_typed(zip, [t.ListType()], t.HomogeneousListType(t.ListType()), variadic=True,
                                             descr="zip returns a list of lists, where the i-th nested list contains the i-th element from each of the input arguments"))

registerBuiltinSP("branch", esr_output(conditionals.branch_request_psp()))
registerBuiltinSP("biplex", no_request(generic_biplex))
registerBuiltinSP("make_csp", typed_nr(csp.MakeCSPOutputPSP(),
                                       [t.HomogeneousArrayType(t.SymbolType()), t.ExpressionType()],
                                       t.AnyType("a compound SP")))

registerBuiltinSP("get_current_environment", typed_func(lambda args: args.env, [], env.EnvironmentType(),
                                                        descr="get_current_environment returns the lexical environment of its invocation site"))
registerBuiltinSP("get_empty_environment", typed_func(lambda args: env.VentureEnvironment(), [], env.EnvironmentType(),
                                                      descr="get_empty_environment returns the empty environment"))
registerBuiltinSP("is_environment", type_test(env.EnvironmentType()))
registerBuiltinSP("extend_environment", typed_nr(eval_sps.ExtendEnvOutputPSP(),
                                                 [env.EnvironmentType(), t.SymbolType(), t.AnyType()],
                                                 env.EnvironmentType()))
registerBuiltinSP("eval",esr_output(TypedPSP(eval_sps.EvalRequestPSP(),
                                             SPType([t.ExpressionType(), env.EnvironmentType()],
                                                    t.RequestType("<object>")))))

registerBuiltinSP("mem",typed_nr(msp.MakeMSPOutputPSP(),
                                 [SPType([t.AnyType("a")], t.AnyType("b"), variadic=True)],
                                 SPType([t.AnyType("a")], t.AnyType("b"), variadic=True)))

registerBuiltinSP("tag", typed_nr(scope.TagOutputPSP(),
                                  # These are type-restricted in Venture, but the actual PSP doesn't care.
                                  [t.AnyType("<scope>"), t.AnyType("<block>"), t.AnyType()],
                                  t.AnyType()))

registerBuiltinSP("tag_exclude", typed_nr(scope.TagExcludeOutputPSP(),
                                          # These are type-restricted in Venture, but the actual PSP doesn't care.
                                          [t.AnyType("<scope>"), t.AnyType()],
                                          t.AnyType()))

registerBuiltinSP("assess", typed_nr(functional.AssessOutputPSP(),
                                     [t.AnyType("<val>"), SPType([t.AnyType("<args>")], t.AnyType("<val>"), variadic=True), t.AnyType("<args>")],
                                     t.NumberType(),
                                     variadic=True))

registerBuiltinSP("binomial", typed_nr(discrete.BinomialOutputPSP(),
                                       [t.CountType(), t.ProbabilityType()], t.CountType()))
registerBuiltinSP("flip", typed_nr(discrete.BernoulliOutputPSP(),
                                   [t.ProbabilityType()], t.BoolType(), min_req_args=0))
registerBuiltinSP("bernoulli", typed_nr(discrete.BernoulliOutputPSP(),
                                        [t.ProbabilityType()], t.IntegerType(), min_req_args=0))
registerBuiltinSP("log_flip", typed_nr(discrete.LogBernoulliOutputPSP(),
                                       [t.NumberType()], t.BoolType()))
registerBuiltinSP("log_bernoulli", typed_nr(discrete.LogBernoulliOutputPSP(), [t.NumberType()], t.BoolType()))
registerBuiltinSP("categorical", typed_nr(discrete.CategoricalOutputPSP(),
                                          [t.SimplexType(), t.ArrayType()], t.AnyType(), min_req_args=1))
registerBuiltinSP("uniform_discrete", typed_nr(discrete.UniformDiscreteOutputPSP(),
                                               [t.IntegerType(), t.IntegerType()], t.IntegerType()))
registerBuiltinSP("poisson", typed_nr(discrete.PoissonOutputPSP(), [t.PositiveType()], t.CountType()))
registerBuiltinSP("normal", no_request(generic_normal))
registerBuiltinSP("vonmises", typed_nr(continuous.VonMisesOutputPSP(),
                                       [t.NumberType(), t.PositiveType()], t.NumberType()))
registerBuiltinSP("uniform_continuous",typed_nr(continuous.UniformOutputPSP(),
                                                [t.NumberType(), t.NumberType()], t.NumberType()))
registerBuiltinSP("beta", typed_nr(continuous.BetaOutputPSP(),
                                   [t.PositiveType(), t.PositiveType()], t.ProbabilityType()))
registerBuiltinSP("expon", typed_nr(continuous.ExponOutputPSP(),
                                    [t.PositiveType()], t.PositiveType()))
registerBuiltinSP("gamma", typed_nr(continuous.GammaOutputPSP(),
                                    [t.PositiveType(), t.PositiveType()], t.PositiveType()))
registerBuiltinSP("student_t", typed_nr(continuous.StudentTOutputPSP(),
                                        [t.PositiveType(), t.NumberType(), t.NumberType()],
                                        t.NumberType(), min_req_args=1 ))
registerBuiltinSP("inv_gamma", typed_nr(continuous.InvGammaOutputPSP(),
                                        [t.PositiveType(), t.PositiveType()], t.PositiveType()))
registerBuiltinSP("laplace", typed_nr(continuous.LaplaceOutputPSP(),
                                      [t.NumberType(), t.PositiveType()], t.NumberType()))

registerBuiltinSP("multivariate_normal", typed_nr(continuous.MVNormalOutputPSP(),
                                                  [t.HomogeneousArrayType(t.NumberType()), t.SymmetricMatrixType()],
                                                  t.HomogeneousArrayType(t.NumberType())))
registerBuiltinSP("inv_wishart", typed_nr(continuous.InverseWishartPSP(),
                                          [t.SymmetricMatrixType(), t.PositiveType()], t.SymmetricMatrixType()))
registerBuiltinSP("wishart", typed_nr(continuous.WishartPSP(),
                                      [t.SymmetricMatrixType(), t.PositiveType()], t.SymmetricMatrixType()))

registerBuiltinSP("make_beta_bernoulli", typed_nr(discrete.MakerCBetaBernoulliOutputPSP(),
                                                  [t.PositiveType(), t.PositiveType()], SPType([], t.BoolType())))
registerBuiltinSP("make_uc_beta_bernoulli", typed_nr(discrete.MakerUBetaBernoulliOutputPSP(),
                                                     [t.PositiveType(), t.PositiveType()], SPType([], t.BoolType())))
registerBuiltinSP("make_suff_stat_bernoulli", typed_nr(discrete.MakerSuffBernoulliOutputPSP(),
                                                       [t.NumberType()], SPType([], t.BoolType())))

registerBuiltinSP("dirichlet", typed_nr(dirichlet.DirichletOutputPSP(),
                                        [t.HomogeneousArrayType(t.PositiveType())], t.SimplexType()))
registerBuiltinSP("symmetric_dirichlet", typed_nr(dirichlet.SymmetricDirichletOutputPSP(),
                                                  [t.PositiveType(), t.CountType()], t.SimplexType()))

registerBuiltinSP("make_dir_mult",
                  typed_nr(dirichlet.MakerCDirMultOutputPSP(),
                           [t.HomogeneousArrayType(t.PositiveType()), t.ArrayType()],
                           SPType([], t.AnyType()), min_req_args=1))
registerBuiltinSP("make_uc_dir_mult",
                  typed_nr(dirichlet.MakerUDirMultOutputPSP(),
                           [t.HomogeneousArrayType(t.PositiveType()), t.ArrayType()],
                           SPType([], t.AnyType()), min_req_args=1))

registerBuiltinSP("make_sym_dir_mult",
                  typed_nr(dirichlet.MakerCSymDirMultOutputPSP(),
                           [t.PositiveType(), t.CountType(), t.ArrayType()],
                           # Saying AnyType here requires the underlying psp to emit a VentureValue.
                           SPType([], t.AnyType()), min_req_args=2))

registerBuiltinSP("make_uc_sym_dir_mult",
                  typed_nr(dirichlet.MakerUSymDirMultOutputPSP(),
                           [t.PositiveType(), t.CountType(), t.ArrayType()],
                           SPType([], t.AnyType()), min_req_args=2))

registerBuiltinSP("make_crp", typed_nr(crp.MakeCRPOutputPSP(),
                                       [t.NumberType(),t.NumberType()], SPType([], t.AtomType()), min_req_args = 1))
registerBuiltinSP("make_lazy_hmm", typed_nr(hmm.MakeUncollapsedHMMOutputPSP(),
                                            [t.SimplexType(), t.MatrixType(), t.MatrixType()],
                                            SPType([t.CountType()], t.AtomType())))
registerBuiltinSP("make_gp", gp.makeGPSP)
registerBuiltinSP("apply_function", function.applyFunctionSP)
registerBuiltinSP("exactly", typed_nr(discrete.ExactlyOutputPSP(),
                                      [t.AnyType(), t.NumberType()], t.AnyType(), min_req_args=1))
registerBuiltinSP("value_error", deterministic_typed(lambda s: raise_(VentureValueError(str(s))),
                                                     [t.AnyType()], t.AnyType()))
