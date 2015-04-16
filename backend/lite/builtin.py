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

import math
import numpy as np
from numbers import Number

from sp import SP, SPType
from psp import NullRequestPSP, ESRRefOutputPSP, DeterministicPSP, TypedPSP

import discrete
import dirichlet
import continuous
import csp
import crp
import cmvn
import function
import gp
import msp
import hmm
import conditionals
import scope
import eval_sps
import functional
import value as v
import env
from utils import careful_exp
from exception import VentureBuiltinSPMethodError

# The types in the value module are generated programmatically, so
# pylint doesn't find out about them.
# pylint: disable=no-member

def builtInValues():
  return { "true" : v.VentureBool(True), "false" : v.VentureBool(False), "nil" : v.VentureNil() }

def no_request(output): return SP(NullRequestPSP(), output)

def esr_output(request): return SP(request, ESRRefOutputPSP())

def typed_nr(output, args_types, return_type, **kwargs):
  return no_request(TypedPSP(output, SPType(args_types, return_type, **kwargs)))

class FunctionPSP(DeterministicPSP):
  def __init__(self, f, descr=None, sim_grad=None):
    self.f = f
    self.descr = descr
    self.sim_grad = sim_grad
    if self.descr is None:
      self.descr = "deterministic %s"
  def simulate(self,args):
    return self.f(args)
  def gradientOfSimulate(self, args, _value, direction):
    # Don't need the value if the function is deterministic, because
    # it consumes no randomness.
    if self.sim_grad:
      return self.sim_grad(args, direction)
    else:
      raise VentureBuiltinSPMethodError("Cannot compute simulation gradient of '%s'" % self.description("<unknown name>"))
  def description(self,name):
    if '%s' in self.descr:
      return self.descr % name
    else:
      return self.descr

def typed_func_psp(f, args_types, return_type, descr=None, sim_grad=None, **kwargs):
  return TypedPSP(FunctionPSP(f, descr, sim_grad), SPType(args_types, return_type, **kwargs))

def typed_func(*args, **kwargs):
  return no_request(typed_func_psp(*args, **kwargs))

# TODO This should actually be named to distinguish it from the
# previous version, which accepts the whole args object (where this
# one splats the operand values).
def deterministic_psp(f, descr=None, sim_grad=None):
  def new_grad(args, direction):
    return sim_grad(args.operandValues, direction)
  return FunctionPSP(lambda args: f(*args.operandValues), descr, sim_grad=(new_grad if sim_grad else None))

def deterministic_typed_psp(f, args_types, return_type, descr=None, sim_grad=None, **kwargs):
  return TypedPSP(deterministic_psp(f, descr, sim_grad), SPType(args_types, return_type, **kwargs))

def deterministic(f, descr=None, sim_grad=None):
  return no_request(deterministic_psp(f, descr, sim_grad))

def deterministic_typed(f, args_types, return_type, descr=None, sim_grad=None, **kwargs):
  return typed_nr(deterministic_psp(f, descr, sim_grad), args_types, return_type, **kwargs)

def binaryNum(f, sim_grad=None, descr=None):
  return deterministic_typed(f, [v.NumberType(), v.NumberType()], v.NumberType(), sim_grad=sim_grad, descr=descr)

def binaryNumS(output):
  return typed_nr(output, [v.NumberType(), v.NumberType()], v.NumberType())

def unaryNum(f, sim_grad=None, descr=None):
  return deterministic_typed(f, [v.NumberType()], v.NumberType(), sim_grad=sim_grad, descr=descr)

def unaryNumS(f):
  return typed_nr(f, [v.NumberType()], v.NumberType())

def naryNum(f, sim_grad=None, descr=None):
  return deterministic_typed(f, [v.NumberType()], v.NumberType(), variadic=True, sim_grad=sim_grad, descr=descr)

def zero_gradient(args, _direction):
  return [0 for _ in args]

def binaryPred(f, descr=None):
  return deterministic_typed(f, [v.AnyType(), v.AnyType()], v.BoolType(), sim_grad=zero_gradient, descr=descr)

def type_test(t):
  return deterministic_typed(lambda thing: thing in t, [v.AnyType()], v.BoolType(),
                             sim_grad = zero_gradient,
                             descr="%s returns true iff its argument is a " + t.name())

def grad_times(args, direction):
  assert len(args) == 2, "Gradient only available for binary multiply"
  return [direction*args[1], direction*args[0]]

def grad_div(args, direction):
  return [direction * (1 / args[1]), direction * (- args[0] / (args[1] * args[1]))]

def grad_sin(args, direction):
  return [direction * math.cos(args[0])]

def grad_cos(args, direction):
  return [-direction * math.sin(args[0])]

def grad_tan(args, direction):
  return [direction * math.pow(math.cos(args[0]), -2)]

def grad_pow(args, direction):
  x, y = args
  return [direction * y * math.pow(x, y - 1), direction * math.log(x) * math.pow(x, y)]

def grad_sqrt(args, direction):
  return [direction * (0.5 / math.sqrt(args[0]))]

def grad_atan2(args, direction):
  (y,x) = args
  denom = x*x + y*y
  return [direction * (x / denom), direction * (-y / denom)]

def grad_list(args, direction):
  if direction == 0:
    return [0 for _ in args]
  else:
    (list_, tail) = direction.asPossiblyImproperList()
    assert tail is None or tail == 0
    tails = [0 for _ in range(len(args) - len(list_))]
    return list_ + tails

def print_(value, label):
  print 'print ' + label + ': ' + str(value)
  return value

def vector_dot(v1, v2):
  candidate = np.dot(v1, v2)
  if isinstance(candidate, Number):  # Numpy! WTF?
    return candidate
  else:
    return 0

def grad_vector_dot(args, direction):
  unscaled = [v.VentureArray(args[1]), v.VentureArray(args[0])]
  return [direction.getNumber() * x for x in unscaled]

builtInSPsList = [
           [ "add",  naryNum(lambda *args: sum(args),
                             sim_grad=lambda args, direction: [direction for _ in args],
                             descr="add returns the sum of all its arguments") ],
           [ "sub", binaryNum(lambda x,y: x - y,
                              sim_grad=lambda args, direction: [direction, -direction],
                              descr="sub returns the difference between its first and second arguments") ],
           [ "mul", naryNum(lambda *args: reduce(lambda x,y: x * y,args,1),
                              sim_grad=grad_times,
                              descr="mul returns the product of all its arguments") ],
           [ "div",   binaryNum(lambda x,y: x / y,
                                sim_grad=grad_div,
                                descr="div returns the quotient of its first argument by its second") ],
           [ "mod",   binaryNum(lambda x,y: x % y,
                                descr="mod returns the modulus of its first argument by its second") ],
           [ "min",   binaryNum(min, descr="min returns the minimum value of its arguments") ],
           [ "eq",    binaryPred(lambda x,y: x.compare(y) == 0,
                                 descr="eq compares its two arguments for equality") ],
           [ "gt",    binaryPred(lambda x,y: x.compare(y) >  0,
                                 descr="gt returns true if its first argument compares greater than its second") ],
           [ "gte",   binaryPred(lambda x,y: x.compare(y) >= 0,
                                 descr="gte returns true if its first argument compares greater than or equal to its second") ],
           [ "lt",    binaryPred(lambda x,y: x.compare(y) <  0,
                                 descr="lt returns true if its first argument compares less than its second") ],
           [ "lte",   binaryPred(lambda x,y: x.compare(y) <= 0,
                                 descr="lte returns true if its first argument compares less than or equal to its second") ],
           [ "floor", unaryNum(math.floor, sim_grad=zero_gradient, descr="floor returns the largest integer less than or equal to its argument (as a VentureNumber)") ],
           # Only makes sense with VentureAtom/VentureNumber distinction
           [ "real",  deterministic_typed(lambda x:x, [v.AtomType()], v.NumberType(),
                                          descr="real returns the identity of its argument atom as a number") ],
           [ "atom_eq", deterministic_typed(lambda x,y: x == y, [v.AtomType(), v.AtomType()], v.BoolType(),
                                            descr="atom_eq tests its two arguments, which must be atoms, for equality") ],
           # If you are wondering about the type signature, this
           # function bootstraps the implicit coersion from numbers to
           # probabilities into an explicit one.  That means that the
           # valid arguments to it are exactly the ones that happen to
           # fall into the range of probabilities.
           [ "probability",  deterministic_typed(lambda x:x, [v.ProbabilityType()], v.ProbabilityType(),
                                                 descr="probability converts its argument to a probability (in direct space)") ],

           [ "sin", unaryNum(math.sin, sim_grad=grad_sin, descr="Returns the sin of its argument") ],
           [ "cos", unaryNum(math.cos, sim_grad=grad_cos, descr="Returns the cos of its argument") ],
           [ "tan", unaryNum(math.tan, sim_grad=grad_tan, descr="Returns the tan of its argument") ],
           [ "hypot", binaryNum(math.hypot, descr="Returns the hypot of its arguments") ],
           [ "exp", unaryNum(careful_exp, sim_grad=lambda args, direction: [direction * careful_exp(args[0])], descr="Returns the exp of its argument") ],
           [ "log", unaryNum(math.log, sim_grad=lambda args, direction: [direction * (1 / float(args[0]))],
                             descr="Returns the log of its argument") ],
           [ "pow", binaryNum(math.pow, sim_grad=grad_pow, descr="pow returns its first argument raised to the power of its second argument") ],
           [ "sqrt", unaryNum(math.sqrt, sim_grad=grad_sqrt, descr="Returns the sqrt of its argument") ],
           [ "atan2", binaryNum(math.atan2,
                                sim_grad=grad_atan2,
                                descr="atan2(y,x) returns the angle from the positive x axis to the point x,y.  The order of arguments is conventional.") ],

           [ "not", deterministic_typed(lambda x: not x, [v.BoolType()], v.BoolType(),
                                        descr="not returns the logical negation of its argument") ],

           [ "is_number", type_test(v.NumberType()) ],
           [ "is_integer", type_test(v.IntegerType()) ],
           [ "is_probability", type_test(v.ProbabilityType()) ],
           [ "is_atom", type_test(v.AtomType()) ],
           [ "is_boolean", type_test(v.BoolType()) ],
           [ "is_symbol", type_test(v.SymbolType()) ],
           [ "is_procedure", type_test(SPType([v.AnyType()], v.AnyType(), variadic=True)) ],

           [ "list", deterministic_typed(lambda *args: args, [v.AnyType()], v.ListType(), variadic=True,
                                         sim_grad=grad_list,
                                         descr="list returns the list of its arguments") ],
           [ "pair", deterministic_typed(lambda a,d: (a,d), [v.AnyType(), v.AnyType()], v.PairType(),
                                         descr="pair returns the pair whose first component is the first argument and whose second component is the second argument") ],
           [ "is_pair", type_test(v.PairType()) ],
           [ "first", deterministic_typed(lambda p: p[0], [v.PairType()], v.AnyType(),
                                          sim_grad=lambda args, direction: [v.VenturePair((direction, 0))],
                                          descr="first returns the first component of its argument pair") ],
           [ "rest", deterministic_typed(lambda p: p[1], [v.PairType()], v.AnyType(),
                                         sim_grad=lambda args, direction: [v.VenturePair((0, direction))],
                                         descr="rest returns the second component of its argument pair") ],
           [ "second", deterministic_typed(lambda p: p[1][0], [v.PairType(second_type=v.PairType())], v.AnyType(),
                                           sim_grad=lambda args, direction: [v.VenturePair((0, v.VenturePair((direction, 0))))],
                                           descr="second returns the first component of the second component of its argument") ],
           [ "to_list", deterministic_typed(lambda seq: seq.asPythonList(), [v.HomogeneousSequenceType(v.AnyType())], v.HomogeneousListType(v.AnyType()),
                                            descr="to_list converts its argument sequence to a list") ],


           [ "array", deterministic_typed(lambda *args: np.array(args), [v.AnyType()], v.ArrayType(), variadic=True,
                                          sim_grad=lambda args, direction: direction.getArray(),
                                          descr="array returns an array initialized with its arguments") ],

           [ "vector", deterministic_typed(lambda *args: np.array(args), [v.NumberType()], v.ArrayUnboxedType(v.NumberType()), variadic=True,
                                          sim_grad=lambda args, direction: direction.getArray(),
                                          descr="vector returns an unboxed numeric array initialized with its arguments") ],

           [ "is_array", type_test(v.ArrayType()) ],
           [ "is_vector", type_test(v.ArrayUnboxedType(v.NumberType())) ],

           [ "to_array", deterministic_typed(lambda seq: seq.getArray(), [v.HomogeneousSequenceType(v.AnyType())], v.HomogeneousArrayType(v.AnyType()),
                                             descr="to_array converts its argument sequence to an array") ],
           [ "to_vector", deterministic_typed(lambda seq: np.array(seq.getArray(v.NumberType())), [v.HomogeneousSequenceType(v.NumberType())], v.ArrayUnboxedType(v.NumberType()),
                                             descr="to_vector converts its argument sequence to a vector") ],

           [ "dict", deterministic_typed(lambda keys, vals: dict(zip(keys, vals)),
                                         [v.HomogeneousListType(v.AnyType("k")), v.HomogeneousListType(v.AnyType("v"))],
                                         v.HomogeneousDictType(v.AnyType("k"), v.AnyType("v")),
                                         descr="dict returns the dictionary mapping the given keys to their respective given values.  It is an error if the given lists are not the same length.") ],
           [ "is_dict", type_test(v.DictType()) ],
           [ "matrix", deterministic_typed(np.array,
                                           [v.HomogeneousListType(v.HomogeneousListType(v.NumberType()))],
                                           v.MatrixType(),
                                           descr="matrix returns a matrix formed from the given list of rows.  It is an error if the given list is not rectangular.") ],
           [ "is_matrix", type_test(v.MatrixType()) ],
           [ "simplex", deterministic_typed(lambda *nums: np.array(nums), [v.ProbabilityType()], v.SimplexType(), variadic=True,
                                            descr="simplex returns the simplex point given by its argument coordinates.") ],
           [ "is_simplex", type_test(v.SimplexType()) ],

           [ "lookup", deterministic_typed(lambda xs, x: xs.lookup(x),
                                           [v.HomogeneousMappingType(v.AnyType("k"), v.AnyType("v")), v.AnyType("k")],
                                           v.AnyType("v"),
                                           sim_grad=lambda args, direction: [args[0].lookup_grad(args[1], direction), 0],
                                           descr="lookup looks the given key up in the given mapping and returns the result.  It is an error if the key is not in the mapping.  Lists and arrays are viewed as mappings from indices to the corresponding elements.  Environments are viewed as mappings from symbols to their values.") ],
           [ "contains", deterministic_typed(lambda xs, x: xs.contains(x),
                                             [v.HomogeneousMappingType(v.AnyType("k"), v.AnyType("v")), v.AnyType("k")],
                                             v.BoolType(),
                                             descr="contains reports whether the given key appears in the given mapping or not.") ],
           [ "size", deterministic_typed(lambda xs: xs.size(),
                                         [v.HomogeneousMappingType(v.AnyType("k"), v.AnyType("v"))],
                                         v.NumberType(),
                                         descr="size returns the number of elements in the given collection (lists and arrays work too)") ],

           [ "arange", deterministic_typed(np.arange,
                                           [v.IntegerType(), v.IntegerType()],
                                           v.ArrayUnboxedType(v.IntegerType()),
                                           min_req_args=1,
                                           descr="(%s [start] stop) returns an array of n consecutive integers from start (inclusive) up to stop (exclusive).")],

           [ "repeat", deterministic_typed(np.repeat,
                                           [v.NumberType(), v.IntegerType()],
                                           v.ArrayUnboxedType(v.NumberType()),
                                           descr="(%s x n) returns an array with the number x repeated n times")],

           [ "linspace", deterministic_typed(np.linspace,
                                             [v.NumberType(), v.NumberType(), v.CountType()],
                                             v.ArrayUnboxedType(v.NumberType()),
                                             descr="(%s start stop n) returns an array of n evenly spaced numbers over the interval [start, stop].") ],

           [ "id_matrix", deterministic_typed(np.identity,
                                              [v.CountType()],
                                              v.MatrixType(),
                                              descr="(%s n) returns an identity matrix of dimension n.") ],

           [ "diag_matrix", deterministic_typed(np.diag,
                                                [v.ArrayUnboxedType(v.NumberType())],
                                                v.MatrixType(),
                                                descr="(%s v) returns a diagonal array whose diagonal is v.") ],

           [ "ravel", deterministic_typed(np.ravel,
                                          [v.MatrixType()],
                                          v.ArrayUnboxedType(v.NumberType()),
                                          descr="(%s m) returns a 1-D array containing the elements of the matrix m.") ],

           [ "vector_dot", deterministic_typed(vector_dot,
                                               [v.ArrayUnboxedType(v.NumberType()), v.ArrayUnboxedType(v.NumberType())],
                                               v.NumberType(),
                                               sim_grad=grad_vector_dot,
                                               descr="(%s x y) returns the dot product of vectors x and y.") ],

           [ "matrix_mul", deterministic_typed(np.dot,
                                               [v.MatrixType(), v.MatrixType()],
                                               v.MatrixType(),
                                               descr="(%s x y) returns the product of matrices x and y.") ],

           [ "print", deterministic_typed(print_,
                                           [v.AnyType("k"), v.SymbolType()],
                                           v.AnyType("k"),
                                           descr = "Print the value of the result of any other SP, labeled by a Symbol.") ],

           [ "apply", esr_output(TypedPSP(functional.ApplyRequestPSP(),
                                          SPType([SPType([v.AnyType("a")], v.AnyType("b"), variadic=True),
                                                  v.HomogeneousArrayType(v.AnyType("a"))],
                                                 v.RequestType("b")))) ],

           [ "mapv", SP(TypedPSP(functional.ArrayMapRequestPSP(),
                                 SPType([SPType([v.AnyType("a")], v.AnyType("b")),
                                         v.HomogeneousArrayType(v.AnyType("a"))],
                                        v.RequestType("<array b>"))),
                        functional.ESRArrayOutputPSP()) ],

           [ "imapv", SP(TypedPSP(functional.IndexedArrayMapRequestPSP(),
                                  SPType([SPType([v.AnyType("index"), v.AnyType("a")], v.AnyType("b")),
                                          v.HomogeneousArrayType(v.AnyType("a"))],
                                         v.RequestType("<array b>"))),
                         functional.ESRArrayOutputPSP()) ],

           [ "zip", deterministic_typed(lambda *args: zip(*args), [v.ListType()], v.HomogeneousListType(v.ListType()), variadic=True,
                                         descr="zip returns a list of lists, where the i-th nested list contains the i-th element from each of the input arguments") ],

           [ "branch", esr_output(conditionals.branch_request_psp()) ],
           [ "biplex", deterministic_typed(lambda p, c, a: c if p else a, [v.BoolType(), v.AnyType(), v.AnyType()], v.AnyType(),
                                           sim_grad=lambda args, direc: [0, direc, 0] if args[0] else [0, 0, direc],
                                           descr="biplex returns either its second or third argument.")],
           [ "make_csp", typed_nr(csp.MakeCSPOutputPSP(),
                                  [v.HomogeneousArrayType(v.SymbolType()), v.ExpressionType()],
                                  v.AnyType("a compound SP")) ],

           [ "get_current_environment", typed_func(lambda args: args.env, [], env.EnvironmentType(),
                                                   descr="get_current_environment returns the lexical environment of its invocation site") ],
           [ "get_empty_environment", typed_func(lambda args: env.VentureEnvironment(), [], env.EnvironmentType(),
                                                 descr="get_empty_environment returns the empty environment") ],
           [ "is_environment", type_test(env.EnvironmentType()) ],
           [ "extend_environment", typed_nr(eval_sps.ExtendEnvOutputPSP(),
                                            [env.EnvironmentType(), v.SymbolType(), v.AnyType()],
                                            env.EnvironmentType()) ],
           [ "eval",esr_output(TypedPSP(eval_sps.EvalRequestPSP(),
                                        SPType([v.ExpressionType(), env.EnvironmentType()],
                                               v.RequestType("<object>")))) ],

           [ "mem",typed_nr(msp.MakeMSPOutputPSP(),
                            [SPType([v.AnyType("a")], v.AnyType("b"), variadic=True)],
                            SPType([v.AnyType("a")], v.AnyType("b"), variadic=True)) ],

           [ "tag", typed_nr(scope.ScopeIncludeOutputPSP(),
                             # These are type-restricted in Venture, but the actual PSP doesn't care.
                             [v.AnyType("<scope>"), v.AnyType("<block>"), v.AnyType()],
                             v.AnyType()) ],

           [ "tag_exclude", typed_nr(scope.ScopeExcludeOutputPSP(),
                                     # These are type-restricted in Venture, but the actual PSP doesn't care.
                                     [v.AnyType("<scope>"), v.AnyType()],
                                     v.AnyType()) ],

           [ "binomial", typed_nr(discrete.BinomialOutputPSP(), [v.CountType(), v.ProbabilityType()], v.CountType()) ],
           [ "flip", typed_nr(discrete.BernoulliOutputPSP(), [v.ProbabilityType()], v.BoolType(), min_req_args=0) ],
           [ "bernoulli", typed_nr(discrete.BernoulliOutputPSP(), [v.ProbabilityType()], v.IntegerType(), min_req_args=0) ],
           [ "log_flip", typed_nr(discrete.LogBernoulliOutputPSP(), [v.NumberType()], v.BoolType()) ],
           [ "log_bernoulli", typed_nr(discrete.LogBernoulliOutputPSP(), [v.NumberType()], v.BoolType()) ],
           [ "categorical", typed_nr(discrete.CategoricalOutputPSP(), [v.SimplexType(), v.ArrayType()], v.AnyType(), min_req_args=1) ],
           [ "uniform_discrete", typed_nr(discrete.UniformDiscreteOutputPSP(), [v.IntegerType(), v.IntegerType()], v.IntegerType()) ],
           [ "poisson", typed_nr(discrete.PoissonOutputPSP(), [v.PositiveType()], v.CountType()) ],
           [ "normal", typed_nr(continuous.NormalOutputPSP(), [v.NumberType(), v.NumberType()], v.NumberType()) ], # TODO Sigma is really non-zero, but negative is OK by scaling
           [ "vonmises", typed_nr(continuous.VonMisesOutputPSP(), [v.NumberType(), v.PositiveType()], v.NumberType()) ],
           [ "uniform_continuous",typed_nr(continuous.UniformOutputPSP(), [v.NumberType(), v.NumberType()], v.NumberType()) ],
           [ "beta", typed_nr(continuous.BetaOutputPSP(), [v.PositiveType(), v.PositiveType()], v.ProbabilityType()) ],
           [ "expon", typed_nr(continuous.ExponOutputPSP(), [v.PositiveType()], v.PositiveType()) ],
           [ "gamma", typed_nr(continuous.GammaOutputPSP(), [v.PositiveType(), v.PositiveType()], v.PositiveType()) ],
           [ "student_t", typed_nr(continuous.StudentTOutputPSP(), [v.PositiveType(), v.NumberType(), v.NumberType()], v.NumberType(), min_req_args=1 ) ],
           [ "inv_gamma", typed_nr(continuous.InvGammaOutputPSP(), [v.PositiveType(), v.PositiveType()], v.PositiveType()) ],
           [ "laplace", typed_nr(continuous.LaplaceOutputPSP(), [v.NumberType(), v.PositiveType()], v.NumberType()) ],

           [ "multivariate_normal", typed_nr(continuous.MVNormalOutputPSP(), [v.HomogeneousArrayType(v.NumberType()), v.SymmetricMatrixType()], v.HomogeneousArrayType(v.NumberType())) ],
           [ "inv_wishart", typed_nr(continuous.InverseWishartPSP(), [v.SymmetricMatrixType(), v.PositiveType()], v.SymmetricMatrixType())],
           [ "wishart", typed_nr(continuous.WishartPSP(), [v.SymmetricMatrixType(), v.PositiveType()], v.SymmetricMatrixType())],

           [ "make_beta_bernoulli",typed_nr(discrete.MakerCBetaBernoulliOutputPSP(), [v.PositiveType(), v.PositiveType()], SPType([], v.BoolType())) ],
           [ "make_uc_beta_bernoulli",typed_nr(discrete.MakerUBetaBernoulliOutputPSP(), [v.PositiveType(), v.PositiveType()], SPType([], v.BoolType())) ],

           [ "dirichlet",typed_nr(dirichlet.DirichletOutputPSP(), [v.HomogeneousArrayType(v.PositiveType())], v.SimplexType()) ],
           [ "symmetric_dirichlet",typed_nr(dirichlet.SymmetricDirichletOutputPSP(), [v.PositiveType(), v.CountType()], v.SimplexType()) ],

           [ "make_dir_mult",typed_nr(dirichlet.MakerCDirMultOutputPSP(), [v.HomogeneousArrayType(v.PositiveType()), v.ArrayType()], SPType([], v.AnyType()), min_req_args=1) ],
           [ "make_uc_dir_mult",typed_nr(dirichlet.MakerUDirMultOutputPSP(), [v.HomogeneousArrayType(v.PositiveType()), v.ArrayType()], SPType([], v.AnyType()), min_req_args=1) ],

           [ "make_sym_dir_mult",typed_nr(dirichlet.MakerCSymDirMultOutputPSP(), [v.PositiveType(), v.CountType(), v.ArrayType()], SPType([], v.AnyType()), min_req_args=2) ], # Saying AnyType here requires the underlying psp to emit a VentureValue.
           [ "make_uc_sym_dir_mult",typed_nr(dirichlet.MakerUSymDirMultOutputPSP(), [v.PositiveType(), v.CountType(), v.ArrayType()], SPType([], v.AnyType()), min_req_args=2) ],

           [ "make_crp",typed_nr(crp.MakeCRPOutputPSP(), [v.NumberType(),v.NumberType()], SPType([], v.AtomType()), min_req_args = 1) ],
           [ "make_cmvn",typed_nr(cmvn.MakeCMVNOutputPSP(),
                                  [v.HomogeneousArrayType(v.NumberType()),v.NumberType(),v.NumberType(),v.MatrixType()],
                                  SPType([], v.HomogeneousArrayType(v.NumberType()))) ],

           [ "make_lazy_hmm",typed_nr(hmm.MakeUncollapsedHMMOutputPSP(), [v.SimplexType(), v.MatrixType(), v.MatrixType()], SPType([v.CountType()], v.AtomType())) ],
           [ "make_gp", gp.makeGPSP ],
           [ "apply_function", function.applyFunctionSP],
           [ "exactly", typed_nr(discrete.ExactlyOutputPSP(), [v.AnyType(), v.NumberType()], v.AnyType(), min_req_args=1)],
]

def builtInSPs():
  return dict(builtInSPsList)
