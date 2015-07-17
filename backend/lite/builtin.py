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
from psp import NullRequestPSP, ESRRefOutputPSP, DeterministicPSP, TypedPSP, DispatchingPSP

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
import types as t
import env
from utils import careful_exp, raise_
from exception import VentureBuiltinSPMethodError, VentureValueError

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
    return sim_grad(args.operandValues(), direction)
  return FunctionPSP(lambda args: f(*args.operandValues()), descr, sim_grad=(new_grad if sim_grad else None))

def deterministic_typed_psp(f, args_types, return_type, descr=None, sim_grad=None, **kwargs):
  return TypedPSP(deterministic_psp(f, descr, sim_grad), SPType(args_types, return_type, **kwargs))

def deterministic(f, descr=None, sim_grad=None):
  return no_request(deterministic_psp(f, descr, sim_grad))

def deterministic_typed(f, args_types, return_type, descr=None, sim_grad=None, **kwargs):
  return typed_nr(deterministic_psp(f, descr, sim_grad), args_types, return_type, **kwargs)

def binaryNum(f, sim_grad=None, descr=None):
  return deterministic_typed(f, [t.NumberType(), t.NumberType()], t.NumberType(), sim_grad=sim_grad, descr=descr)

def binaryNumS(output):
  return typed_nr(output, [t.NumberType(), t.NumberType()], t.NumberType())

def unaryNum(f, sim_grad=None, descr=None):
  return deterministic_typed(f, [t.NumberType()], t.NumberType(), sim_grad=sim_grad, descr=descr)

def unaryNumS(f):
  return typed_nr(f, [t.NumberType()], t.NumberType())

def naryNum(f, sim_grad=None, descr=None):
  return deterministic_typed(f, [t.NumberType()], t.NumberType(), variadic=True, sim_grad=sim_grad, descr=descr)

def zero_gradient(args, _direction):
  return [0 for _ in args]

def binaryPred(f, descr=None):
  return deterministic_typed(f, [t.AnyType(), t.AnyType()], t.BoolType(), sim_grad=zero_gradient, descr=descr)

def type_test(tp):
  return deterministic_typed(lambda thing: thing in tp, [t.AnyType()], t.BoolType(),
                             sim_grad = zero_gradient,
                             descr="%s returns true iff its argument is a " + tp.name())

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
  unscaled = [v.VentureArray(args[1]), v.VentureArray(args[0])]
  return [direction.getNumber() * x for x in unscaled]

generic_add = DispatchingPSP([SPType([t.NumberType()], t.NumberType(), variadic=True),
                              SPType([t.ArrayUnboxedType(t.NumberType())], t.ArrayUnboxedType(t.NumberType()), variadic=True)],
                             [TypedPSP(deterministic_psp(lambda *args: sum(args),
                                                         sim_grad=lambda args, direction: [direction for _ in args],
                                                         descr="add returns the sum of all its arguments"),
                                       SPType([t.NumberType()], t.NumberType(), variadic=True)),
                              TypedPSP(deterministic_psp(lambda *args: np.sum(args, axis=0),
                                                         sim_grad=lambda args, direction: [direction for _ in args],
                                                         descr="add returns the sum of all its arguments"),
                                       SPType([t.ArrayUnboxedType(t.NumberType())], t.ArrayUnboxedType(t.NumberType()), variadic=True))])

builtInSPsList = [
           [ "add", no_request(generic_add)],
           [ "sub", binaryNum(lambda x,y: x - y,
                              sim_grad=lambda args, direction: [direction, -direction],
                              descr="sub returns the difference between its first and second arguments") ],
           [ "mul", naryNum(lambda *args: reduce(lambda x,y: x * y,args,1),
                              sim_grad=grad_times,
                              descr="mul returns the product of all its arguments") ],
           [ "div",   binaryNum(lambda x,y: x / y,
                                sim_grad=grad_div,
                                descr="div returns the ratio of its first argument to its second") ],
           [ "int_div",   binaryNum(lambda x,y: raise_(VentureValueError("division by zero")) if int(y) == 0 else int(x) // int(y),
                                    descr="div returns the integer quotient of its first argument by its second") ],
           [ "int_mod",   binaryNum(lambda x,y: raise_(VentureValueError("modulo by zero")) if int(y) == 0 else int(x) % int(y),
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
           [ "real",  deterministic_typed(lambda x:x, [t.AtomType()], t.NumberType(),
                                          descr="real returns the identity of its argument atom as a number") ],
           [ "atom_eq", deterministic_typed(lambda x,y: x == y, [t.AtomType(), t.AtomType()], t.BoolType(),
                                            descr="atom_eq tests its two arguments, which must be atoms, for equality") ],
           # If you are wondering about the type signature, this
           # function bootstraps the implicit coersion from numbers to
           # probabilities into an explicit one.  That means that the
           # valid arguments to it are exactly the ones that happen to
           # fall into the range of probabilities.
           [ "probability",  deterministic_typed(lambda x:x, [t.ProbabilityType()], t.ProbabilityType(),
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

           [ "not", deterministic_typed(lambda x: not x, [t.BoolType()], t.BoolType(),
                                        descr="not returns the logical negation of its argument") ],
           [ "xor", deterministic_typed(lambda x, y: x != y, [t.BoolType(), t.BoolType()], t.BoolType(),
                                        descr="xor(x,y) returns true if exactly one of x and y is true") ],
                                        
           [ "is_number", type_test(t.NumberType()) ],
           [ "is_integer", type_test(t.IntegerType()) ],
           [ "is_probability", type_test(t.ProbabilityType()) ],
           [ "is_atom", type_test(t.AtomType()) ],
           [ "is_boolean", type_test(t.BoolType()) ],
           [ "is_symbol", type_test(t.SymbolType()) ],
           [ "is_procedure", type_test(SPType([t.AnyType()], t.AnyType(), variadic=True)) ],

           [ "list", deterministic_typed(lambda *args: args, [t.AnyType()], t.ListType(), variadic=True,
                                         sim_grad=grad_list,
                                         descr="list returns the list of its arguments") ],
           [ "pair", deterministic_typed(lambda a,d: (a,d), [t.AnyType(), t.AnyType()], t.PairType(),
                                         descr="pair returns the pair whose first component is the first argument and whose second component is the second argument") ],
           [ "is_pair", type_test(t.PairType()) ],
           [ "first", deterministic_typed(lambda p: p[0], [t.PairType()], t.AnyType(),
                                          sim_grad=lambda args, direction: [v.VenturePair((direction, 0))],
                                          descr="first returns the first component of its argument pair") ],
           [ "rest", deterministic_typed(lambda p: p[1], [t.PairType()], t.AnyType(),
                                         sim_grad=lambda args, direction: [v.VenturePair((0, direction))],
                                         descr="rest returns the second component of its argument pair") ],
           [ "second", deterministic_typed(lambda p: p[1][0], [t.PairType(second_type=t.PairType())], t.AnyType(),
                                           sim_grad=lambda args, direction: [v.VenturePair((0, v.VenturePair((direction, 0))))],
                                           descr="second returns the first component of the second component of its argument") ],
           [ "to_list", deterministic_typed(lambda seq: seq.asPythonList(), [t.HomogeneousSequenceType(t.AnyType())], t.HomogeneousListType(t.AnyType()),
                                            descr="to_list converts its argument sequence to a list") ],


           [ "array", deterministic_typed(lambda *args: np.array(args), [t.AnyType()], t.ArrayType(), variadic=True,
                                          sim_grad=lambda args, direction: direction.getArray(),
                                          descr="array returns an array initialized with its arguments") ],

           [ "vector", deterministic_typed(lambda *args: np.array(args), [t.NumberType()], t.ArrayUnboxedType(t.NumberType()), variadic=True,
                                          sim_grad=lambda args, direction: direction.getArray(),
                                          descr="vector returns an unboxed numeric array initialized with its arguments") ],

           [ "is_array", type_test(t.ArrayType()) ],
           [ "is_vector", type_test(t.ArrayUnboxedType(t.NumberType())) ],

           [ "to_array", deterministic_typed(lambda seq: seq.getArray(), [t.HomogeneousSequenceType(t.AnyType())], t.HomogeneousArrayType(t.AnyType()),
                                             descr="to_array converts its argument sequence to an array") ],
           [ "to_vector", deterministic_typed(lambda seq: np.array(seq.getArray(t.NumberType())), [t.HomogeneousSequenceType(t.NumberType())], t.ArrayUnboxedType(t.NumberType()),
                                             descr="to_vector converts its argument sequence to a vector") ],

           [ "dict", deterministic_typed(lambda keys, vals: dict(zip(keys, vals)),
                                         [t.HomogeneousListType(t.AnyType("k")), t.HomogeneousListType(t.AnyType("v"))],
                                         t.HomogeneousDictType(t.AnyType("k"), t.AnyType("v")),
                                         descr="dict returns the dictionary mapping the given keys to their respective given values.  It is an error if the given lists are not the same length.") ],
           [ "is_dict", type_test(t.DictType()) ],
           [ "matrix", deterministic_typed(np.array,
                                           [t.HomogeneousListType(t.HomogeneousListType(t.NumberType()))],
                                           t.MatrixType(),
                                           descr="matrix returns a matrix formed from the given list of rows.  It is an error if the given list is not rectangular.") ],
           [ "is_matrix", type_test(t.MatrixType()) ],
           [ "simplex", deterministic_typed(lambda *nums: np.array(nums), [t.ProbabilityType()], t.SimplexType(), variadic=True,
                                            descr="simplex returns the simplex point given by its argument coordinates.") ],
           [ "is_simplex", type_test(t.SimplexType()) ],

           [ "lookup", deterministic_typed(lambda xs, x: xs.lookup(x),
                                           [t.HomogeneousMappingType(t.AnyType("k"), t.AnyType("v")), t.AnyType("k")],
                                           t.AnyType("v"),
                                           sim_grad=lambda args, direction: [args[0].lookup_grad(args[1], direction), 0],
                                           descr="lookup looks the given key up in the given mapping and returns the result.  It is an error if the key is not in the mapping.  Lists and arrays are viewed as mappings from indices to the corresponding elements.  Environments are viewed as mappings from symbols to their values.") ],
           [ "contains", deterministic_typed(lambda xs, x: xs.contains(x),
                                             [t.HomogeneousMappingType(t.AnyType("k"), t.AnyType("v")), t.AnyType("k")],
                                             t.BoolType(),
                                             descr="contains reports whether the given key appears in the given mapping or not.") ],
           [ "size", deterministic_typed(lambda xs: xs.size(),
                                         [t.HomogeneousMappingType(t.AnyType("k"), t.AnyType("v"))],
                                         t.NumberType(),
                                         descr="size returns the number of elements in the given collection (lists and arrays work too)") ],
           [ "take", deterministic_typed(lambda ind, xs: xs.take(ind),
                                         [t.IntegerType(), t.HomogeneousSequenceType(t.AnyType("k"))],
                                         t.HomogeneousSequenceType(t.AnyType("k")),
                                         descr="take returns the requested number of elements from the beginning of the given sequence, as another sequence of the same type.") ],

           [ "arange", deterministic_typed(np.arange,
                                           [t.IntegerType(), t.IntegerType()],
                                           t.ArrayUnboxedType(t.IntegerType()),
                                           min_req_args=1,
                                           descr="(%s [start] stop) returns an array of n consecutive integers from start (inclusive) up to stop (exclusive).")],

           [ "fill", deterministic_typed(np.full,
                                         [t.IntegerType(), t.NumberType()],
                                         t.ArrayUnboxedType(t.NumberType()),
                                         descr="(%s n x) returns an array with the number x repeated n times")],

           [ "linspace", deterministic_typed(np.linspace,
                                             [t.NumberType(), t.NumberType(), t.CountType()],
                                             t.ArrayUnboxedType(t.NumberType()),
                                             descr="(%s start stop n) returns an array of n evenly spaced numbers over the interval [start, stop].") ],

           [ "id_matrix", deterministic_typed(np.identity,
                                              [t.CountType()],
                                              t.MatrixType(),
                                              descr="(%s n) returns an identity matrix of dimension n.") ],

           [ "diag_matrix", deterministic_typed(np.diag,
                                                [t.ArrayUnboxedType(t.NumberType())],
                                                t.MatrixType(),
                                                descr="(%s v) returns a diagonal array whose diagonal is v.") ],

           [ "ravel", deterministic_typed(np.ravel,
                                          [t.MatrixType()],
                                          t.ArrayUnboxedType(t.NumberType()),
                                          descr="(%s m) returns a 1-D array containing the elements of the matrix m.") ],

           [ "transpose", deterministic_typed(np.transpose,
                                              [t.MatrixType()],
                                              t.MatrixType(),
                                              descr="(%s m) returns the transpose of the matrix m.") ],

           [ "vector_add", deterministic_typed(np.add,
                                               [t.ArrayUnboxedType(t.NumberType()), t.ArrayUnboxedType(t.NumberType())],
                                               t.ArrayUnboxedType(t.NumberType()),
                                               descr="(%s x y) returns the sum of vectors x and y.") ],

           [ "matrix_add", deterministic_typed(np.add,
                                               [t.MatrixType(), t.MatrixType()],
                                               t.MatrixType(),
                                               descr="(%s x y) returns the sum of matrices x and y.") ],

           [ "scale_vector", deterministic_typed(np.multiply,
                                                 [t.NumberType(), t.ArrayUnboxedType(t.NumberType())],
                                                 t.ArrayUnboxedType(t.NumberType()),
                                                 descr="(%s x y) returns the product of scalar x and vector y.") ],

           [ "scale_matrix", deterministic_typed(np.multiply,
                                                 [t.NumberType(), t.MatrixType()],
                                                 t.MatrixType(),
                                                 descr="(%s x y) returns the product of scalar x and matrix y.") ],

           [ "vector_dot", deterministic_typed(vector_dot,
                                               [t.ArrayUnboxedType(t.NumberType()), t.ArrayUnboxedType(t.NumberType())],
                                               t.NumberType(),
                                               sim_grad=grad_vector_dot,
                                               descr="(%s x y) returns the dot product of vectors x and y.") ],

           [ "matrix_mul", deterministic_typed(np.dot,
                                               [t.MatrixType(), t.MatrixType()],
                                               t.MatrixType(),
                                               descr="(%s x y) returns the product of matrices x and y.") ],

           [ "matrix_times_vector",
             deterministic_typed(np.dot,
                                 [t.MatrixType(), t.ArrayUnboxedType(t.NumberType())],
                                 t.ArrayUnboxedType(t.NumberType()),
                                 descr="(%s M v) returns the matrix-vector product Mv.") ],

           [ "vector_times_matrix",
             deterministic_typed(np.dot,
                                 [t.ArrayUnboxedType(t.NumberType()), t.MatrixType()],
                                 t.ArrayUnboxedType(t.NumberType()),
                                 descr="(%s v M) returns the vector-matrix product vM.") ],

           [ "debug", deterministic_typed(debug_print,
                                           [t.SymbolType(), t.AnyType("k")],
                                           t.AnyType("k"),
                                           descr = "Print the given value, labeled by a Symbol. Return the value. Intended for debugging or for monitoring execution.") ],

           [ "apply", esr_output(TypedPSP(functional.ApplyRequestPSP(),
                                          SPType([SPType([t.AnyType("a")], t.AnyType("b"), variadic=True),
                                                  t.HomogeneousArrayType(t.AnyType("a"))],
                                                 t.RequestType("b")))) ],

           [ "fix", SP(TypedPSP(functional.FixRequestPSP(),
                                SPType([t.HomogeneousArrayType(t.SymbolType()),
                                        t.HomogeneousArrayType(t.ExpressionType())],
                                       t.RequestType())),
                       TypedPSP(functional.FixOutputPSP(),
                                SPType([t.HomogeneousArrayType(t.SymbolType()),
                                        t.HomogeneousArrayType(t.ExpressionType())],
                                       env.EnvironmentType()))) ],

           [ "mapv", SP(TypedPSP(functional.ArrayMapRequestPSP(),
                                 SPType([SPType([t.AnyType("a")], t.AnyType("b")),
                                         t.HomogeneousArrayType(t.AnyType("a"))],
                                        t.RequestType("<array b>"))),
                        functional.ESRArrayOutputPSP()) ],

           [ "imapv", SP(TypedPSP(functional.IndexedArrayMapRequestPSP(),
                                  SPType([SPType([t.AnyType("index"), t.AnyType("a")], t.AnyType("b")),
                                          t.HomogeneousArrayType(t.AnyType("a"))],
                                         t.RequestType("<array b>"))),
                         functional.ESRArrayOutputPSP()) ],

           [ "zip", deterministic_typed(zip, [t.ListType()], t.HomogeneousListType(t.ListType()), variadic=True,
                                        descr="zip returns a list of lists, where the i-th nested list contains the i-th element from each of the input arguments") ],

           [ "branch", esr_output(conditionals.branch_request_psp()) ],
           [ "biplex", deterministic_typed(lambda p, c, a: c if p else a, [t.BoolType(), t.AnyType(), t.AnyType()], t.AnyType(),
                                           sim_grad=lambda args, direc: [0, direc, 0] if args[0] else [0, 0, direc],
                                           descr="biplex returns either its second or third argument.")],
           [ "make_csp", typed_nr(csp.MakeCSPOutputPSP(),
                                  [t.HomogeneousArrayType(t.SymbolType()), t.ExpressionType()],
                                  t.AnyType("a compound SP")) ],

           [ "get_current_environment", typed_func(lambda args: args.env, [], env.EnvironmentType(),
                                                   descr="get_current_environment returns the lexical environment of its invocation site") ],
           [ "get_empty_environment", typed_func(lambda args: env.VentureEnvironment(), [], env.EnvironmentType(),
                                                 descr="get_empty_environment returns the empty environment") ],
           [ "is_environment", type_test(env.EnvironmentType()) ],
           [ "extend_environment", typed_nr(eval_sps.ExtendEnvOutputPSP(),
                                            [env.EnvironmentType(), t.SymbolType(), t.AnyType()],
                                            env.EnvironmentType()) ],
           [ "eval",esr_output(TypedPSP(eval_sps.EvalRequestPSP(),
                                        SPType([t.ExpressionType(), env.EnvironmentType()],
                                               t.RequestType("<object>")))) ],

           [ "mem",typed_nr(msp.MakeMSPOutputPSP(),
                            [SPType([t.AnyType("a")], t.AnyType("b"), variadic=True)],
                            SPType([t.AnyType("a")], t.AnyType("b"), variadic=True)) ],

           [ "tag", typed_nr(scope.TagOutputPSP(),
                             # These are type-restricted in Venture, but the actual PSP doesn't care.
                             [t.AnyType("<scope>"), t.AnyType("<block>"), t.AnyType()],
                             t.AnyType()) ],

           [ "tag_exclude", typed_nr(scope.TagExcludeOutputPSP(),
                                     # These are type-restricted in Venture, but the actual PSP doesn't care.
                                     [t.AnyType("<scope>"), t.AnyType()],
                                     t.AnyType()) ],

           [ "assess", typed_nr(functional.AssessOutputPSP(),
                                [t.AnyType("<val>"), SPType([t.AnyType("<args>")], t.AnyType("<val>"), variadic=True), t.AnyType("<args>")],
                                t.NumberType(),
                                variadic=True) ],

           [ "binomial", typed_nr(discrete.BinomialOutputPSP(), [t.CountType(), t.ProbabilityType()], t.CountType()) ],
           [ "flip", typed_nr(discrete.BernoulliOutputPSP(), [t.ProbabilityType()], t.BoolType(), min_req_args=0) ],
           [ "bernoulli", typed_nr(discrete.BernoulliOutputPSP(), [t.ProbabilityType()], t.IntegerType(), min_req_args=0) ],
           [ "log_flip", typed_nr(discrete.LogBernoulliOutputPSP(), [t.NumberType()], t.BoolType()) ],
           [ "log_bernoulli", typed_nr(discrete.LogBernoulliOutputPSP(), [t.NumberType()], t.BoolType()) ],
           [ "categorical", typed_nr(discrete.CategoricalOutputPSP(), [t.SimplexType(), t.ArrayType()], t.AnyType(), min_req_args=1) ],
           [ "uniform_discrete", typed_nr(discrete.UniformDiscreteOutputPSP(), [t.IntegerType(), t.IntegerType()], t.IntegerType()) ],
           [ "poisson", typed_nr(discrete.PoissonOutputPSP(), [t.PositiveType()], t.CountType()) ],
           [ "normal", typed_nr(continuous.NormalOutputPSP(), [t.NumberType(), t.NumberType()], t.NumberType()) ], # TODO Sigma is really non-zero, but negative is OK by scaling
           [ "vonmises", typed_nr(continuous.VonMisesOutputPSP(), [t.NumberType(), t.PositiveType()], t.NumberType()) ],
           [ "uniform_continuous",typed_nr(continuous.UniformOutputPSP(), [t.NumberType(), t.NumberType()], t.NumberType()) ],
           [ "beta", typed_nr(continuous.BetaOutputPSP(), [t.PositiveType(), t.PositiveType()], t.ProbabilityType()) ],
           [ "expon", typed_nr(continuous.ExponOutputPSP(), [t.PositiveType()], t.PositiveType()) ],
           [ "gamma", typed_nr(continuous.GammaOutputPSP(), [t.PositiveType(), t.PositiveType()], t.PositiveType()) ],
           [ "student_t", typed_nr(continuous.StudentTOutputPSP(), [t.PositiveType(), t.NumberType(), t.NumberType()], t.NumberType(), min_req_args=1 ) ],
           [ "inv_gamma", typed_nr(continuous.InvGammaOutputPSP(), [t.PositiveType(), t.PositiveType()], t.PositiveType()) ],
           [ "laplace", typed_nr(continuous.LaplaceOutputPSP(), [t.NumberType(), t.PositiveType()], t.NumberType()) ],

           [ "multivariate_normal", typed_nr(continuous.MVNormalOutputPSP(), [t.HomogeneousArrayType(t.NumberType()), t.SymmetricMatrixType()], t.HomogeneousArrayType(t.NumberType())) ],
           [ "inv_wishart", typed_nr(continuous.InverseWishartPSP(), [t.SymmetricMatrixType(), t.PositiveType()], t.SymmetricMatrixType())],
           [ "wishart", typed_nr(continuous.WishartPSP(), [t.SymmetricMatrixType(), t.PositiveType()], t.SymmetricMatrixType())],

           [ "make_beta_bernoulli",typed_nr(discrete.MakerCBetaBernoulliOutputPSP(), [t.PositiveType(), t.PositiveType()], SPType([], t.BoolType())) ],
           [ "make_uc_beta_bernoulli",typed_nr(discrete.MakerUBetaBernoulliOutputPSP(), [t.PositiveType(), t.PositiveType()], SPType([], t.BoolType())) ],
           [ "make_suff_stat_bernoulli",typed_nr(discrete.MakerSuffBernoulliOutputPSP(), [t.NumberType()], SPType([], t.BoolType())) ],

           [ "dirichlet",typed_nr(dirichlet.DirichletOutputPSP(), [t.HomogeneousArrayType(t.PositiveType())], t.SimplexType()) ],
           [ "symmetric_dirichlet",typed_nr(dirichlet.SymmetricDirichletOutputPSP(), [t.PositiveType(), t.CountType()], t.SimplexType()) ],

           [ "make_dir_mult",typed_nr(dirichlet.MakerCDirMultOutputPSP(), [t.HomogeneousArrayType(t.PositiveType()), t.ArrayType()], SPType([], t.AnyType()), min_req_args=1) ],
           [ "make_uc_dir_mult",typed_nr(dirichlet.MakerUDirMultOutputPSP(), [t.HomogeneousArrayType(t.PositiveType()), t.ArrayType()], SPType([], t.AnyType()), min_req_args=1) ],

           [ "make_sym_dir_mult",typed_nr(dirichlet.MakerCSymDirMultOutputPSP(), [t.PositiveType(), t.CountType(), t.ArrayType()], SPType([], t.AnyType()), min_req_args=2) ], # Saying AnyType here requires the underlying psp to emit a VentureValue.
           [ "make_uc_sym_dir_mult",typed_nr(dirichlet.MakerUSymDirMultOutputPSP(), [t.PositiveType(), t.CountType(), t.ArrayType()], SPType([], t.AnyType()), min_req_args=2) ],

           [ "make_crp",typed_nr(crp.MakeCRPOutputPSP(), [t.NumberType(),t.NumberType()], SPType([], t.AtomType()), min_req_args = 1) ],
           [ "make_cmvn",typed_nr(cmvn.MakeCMVNOutputPSP(),
                                  [t.HomogeneousArrayType(t.NumberType()),t.NumberType(),t.NumberType(),t.MatrixType()],
                                  SPType([], t.HomogeneousArrayType(t.NumberType()))) ],

           [ "make_lazy_hmm",typed_nr(hmm.MakeUncollapsedHMMOutputPSP(), [t.SimplexType(), t.MatrixType(), t.MatrixType()], SPType([t.CountType()], t.AtomType())) ],
           [ "make_gp", gp.makeGPSP ],
           [ "apply_function", function.applyFunctionSP],
           [ "exactly", typed_nr(discrete.ExactlyOutputPSP(), [t.AnyType(), t.NumberType()], t.AnyType(), min_req_args=1)],
           [ "value_error", deterministic_typed(lambda s: raise_(VentureValueError(str(s))), [t.AnyType()], t.AnyType())]
]

def builtInSPs():
  return dict(builtInSPsList)
