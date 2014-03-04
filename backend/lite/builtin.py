import math
import numpy as np

from sp import VentureSP
from psp import NullRequestPSP, ESRRefOutputPSP, PSP, TypedPSP

import discrete
import continuous
import dstructures
import csp
import crp
import msp
import hmm
import conditionals
import scope
import eval_sps
import value as v
import env

# The types in the value module are generated programmatically, so
# pylint doesn't find out about them.
# pylint: disable=no-member

def builtInValues():
  return { "true" : v.VentureBool(True), "false" : v.VentureBool(False) }

def no_request(output): return VentureSP(NullRequestPSP(), output)

def typed_nr(output, args_types, return_type, **kwargs):
  return no_request(TypedPSP(args_types, return_type, output, **kwargs))

def deterministic_psp(f, descr=None):
  class DeterministicPSP(PSP):
    def __init__(self, descr):
      self.descr = descr
      if self.descr is None:
        self.descr = "deterministic %s"
    def simulate(self,args):
      return f(*args.operandValues)
    def description(self,name):
      return self.descr % name
  return DeterministicPSP(descr)

def deterministic(f, descr=None):
  return no_request(deterministic_psp(f, descr))

def deterministic_typed(f, args_types, return_type, descr=None, **kwargs):
  return typed_nr(deterministic_psp(f, descr), args_types, return_type, **kwargs)

def binaryNum(f, descr=None):
  return deterministic_typed(f, [v.NumberType(), v.NumberType()], v.NumberType(), descr=descr)

def binaryNumS(output):
  return typed_nr(output, [v.NumberType(), v.NumberType()], v.NumberType())

def unaryNum(f, descr=None):
  return deterministic_typed(f, [v.NumberType()], v.NumberType(), descr=descr)

def unaryNumS(f):
  return typed_nr(f, [v.NumberType()], v.NumberType())

def naryNum(f, descr=None):
  return deterministic_typed(f, [v.NumberType()], v.NumberType(), variadic=True, descr=descr)

def type_test(t):
  return deterministic(lambda thing: v.VentureBool(isinstance(thing, t)))

def builtInSPsList():
  return [ [ "plus",  naryNum(lambda *args: sum(args)) ],
           [ "minus", binaryNum(lambda x,y: x - y) ],
           [ "times", naryNum(lambda *args: reduce(lambda x,y: x * y,args,1)) ],
           [ "div",   binaryNum(lambda x,y: x / y) ],
           [ "eq",    deterministic(lambda x,y: v.VentureBool(x.compare(y) == 0)) ],
           [ "gt",    deterministic(lambda x,y: v.VentureBool(x.compare(y) >  0)) ],
           [ "gte",   deterministic(lambda x,y: v.VentureBool(x.compare(y) >= 0)) ],
           [ "lt",    deterministic(lambda x,y: v.VentureBool(x.compare(y) <  0)) ],
           [ "lte",   deterministic(lambda x,y: v.VentureBool(x.compare(y) <= 0)) ],
           # Only makes sense with VentureAtom/VentureNumber distinction
           [ "real",  deterministic_typed(lambda x:x, [v.AtomType()], v.NumberType()) ],
           # Atoms appear to be represented as Python integers
           [ "atom_eq", deterministic_typed(lambda x,y: x == y, [v.AtomType(), v.AtomType()], v.BoolType()) ],

           [ "sin", unaryNum(math.sin) ],
           [ "cos", unaryNum(math.cos) ],
           [ "tan", unaryNum(math.tan) ],
           [ "hypot", unaryNum(math.hypot) ],
           [ "exp", unaryNum(math.exp) ],
           [ "log", unaryNum(math.log) ],
           [ "pow", unaryNum(math.pow) ],
           [ "sqrt", unaryNum(math.sqrt) ],

           [ "not", deterministic_typed(lambda x: not x, [v.BoolType()], v.BoolType()) ],

           [ "is_symbol", type_test(v.VentureSymbol) ],
           [ "is_atom", type_test(v.VentureAtom) ],

           [ "list", deterministic(v.pythonListToVentureList) ],
           [ "pair", deterministic(v.VenturePair) ],
           [ "is_pair", type_test(v.VenturePair) ],
           [ "first", deterministic_typed(lambda p: p[0], [v.PairType()], v.AnyType()) ],
           [ "rest", deterministic_typed(lambda p: p[1], [v.PairType()], v.AnyType()) ],
           [ "second", deterministic_typed(lambda p: p[1].first, [v.PairType()], v.AnyType()) ],

           [ "map_list",VentureSP(dstructures.MapListRequestPSP(),dstructures.MapListOutputPSP()) ],

           [ "array", deterministic(lambda *args: v.VentureArray(np.array(args))) ],
           [ "is_array", type_test(v.VentureArray) ],
           [ "dict", no_request(dstructures.DictOutputPSP()) ],
           [ "is_dict", type_test(v.VentureDict) ],
           [ "matrix", deterministic(lambda rows: v.VentureMatrix(np.mat([[val.getNumber() for val in row.asPythonList()] for row in rows.asPythonList()]))) ], # TODO Put in the description that the input is a list of the rows of the matrix
           [ "is_matrix", type_test(v.VentureMatrix) ],
           [ "simplex", deterministic_typed(lambda *nums: np.array(nums), [v.NumberType()], v.SimplexType(), variadic=True) ],
           [ "is_simplex", type_test(v.VentureSimplex) ],

           [ "lookup", deterministic(lambda xs, x: xs.lookup(x)) ],
           [ "contains", deterministic(lambda xs, x: v.VentureBool(xs.contains(x))) ],
           [ "size", deterministic(lambda xs: v.VentureNumber(xs.size())) ],

           [ "branch", VentureSP(conditionals.BranchRequestPSP(),ESRRefOutputPSP()) ],
           [ "biplex", deterministic_typed(lambda p, c, a: c if p else a, [v.BoolType(), v.AnyType(), v.AnyType()], v.AnyType())],
           [ "make_csp", no_request(csp.MakeCSPOutputPSP()) ],

           [ "get_current_environment",no_request(eval_sps.GetCurrentEnvOutputPSP()) ],
           [ "get_empty_environment",no_request(eval_sps.GetEmptyEnvOutputPSP()) ],
           [ "is_environment", type_test(env.VentureEnvironment) ],
           [ "extend_environment",no_request(eval_sps.ExtendEnvOutputPSP()) ],
           [ "eval",VentureSP(eval_sps.EvalRequestPSP(),ESRRefOutputPSP()) ],

           [ "mem",no_request(msp.MakeMSPOutputPSP()) ],

           [ "scope_include",no_request(scope.ScopeIncludeOutputPSP()) ],

           [ "binomial", binaryNumS(discrete.BinomialOutputPSP()) ],
           [ "flip", typed_nr(discrete.BernoulliOutputPSP(), [v.NumberType()], v.BoolType(), min_req_args=0) ],
           [ "bernoulli", typed_nr(discrete.BernoulliOutputPSP(), [v.NumberType()], v.BoolType(), min_req_args=0) ],
           [ "categorical", typed_nr(discrete.CategoricalOutputPSP(), [v.SimplexType(), v.ArrayType()], v.AnyType(), min_req_args=1) ],

           [ "normal",binaryNumS(continuous.NormalOutputPSP()) ],
           [ "uniform_continuous",binaryNumS(continuous.UniformOutputPSP()) ],
           [ "beta",binaryNumS(continuous.BetaOutputPSP()) ],
           [ "gamma",binaryNumS(continuous.GammaOutputPSP()) ],
           [ "student_t",unaryNumS(continuous.StudentTOutputPSP()) ],

           [ "dirichlet",typed_nr(discrete.DirichletOutputPSP(), [v.HomogeneousArrayType(v.NumberType())], v.SimplexType()) ],
           [ "symmetric_dirichlet",typed_nr(discrete.SymmetricDirichletOutputPSP(), [v.NumberType(), v.NumberType()], v.SimplexType()) ],

           [ "make_dir_mult",typed_nr(discrete.MakerCDirMultOutputPSP(), [v.HomogeneousArrayType(v.NumberType()), v.ArrayType()], v.AnyType(), min_req_args=1) ],
           [ "make_uc_dir_mult",typed_nr(discrete.MakerUDirMultOutputPSP(), [v.HomogeneousArrayType(v.NumberType()), v.ArrayType()], v.AnyType(), min_req_args=1) ],

           [ "make_sym_dir_mult",typed_nr(discrete.MakerCSymDirMultOutputPSP(), [v.NumberType(), v.NumberType(), v.ArrayType()], v.AnyType(), min_req_args=2) ], # Saying AnyType here requires the underlying psp to emit a VentureValue.
           [ "make_uc_sym_dir_mult",typed_nr(discrete.MakerUSymDirMultOutputPSP(), [v.NumberType(), v.NumberType(), v.ArrayType()], v.AnyType(), min_req_args=2) ],

           [ "make_beta_bernoulli",typed_nr(discrete.MakerCBetaBernoulliOutputPSP(), [v.NumberType(), v.NumberType()], v.AnyType()) ],
           [ "make_uc_beta_bernoulli",typed_nr(discrete.MakerUBetaBernoulliOutputPSP(), [v.NumberType(), v.NumberType()], v.AnyType()) ],

           [ "make_crp",typed_nr(crp.MakeCRPOutputPSP(), [v.NumberType()], v.AnyType()) ],

           [ "make_lazy_hmm",typed_nr(hmm.MakeUncollapsedHMMOutputPSP(), [v.SimplexType(), v.MatrixType(), v.MatrixType()], v.AnyType()) ],
  ]

def builtInSPs():
  return dict(builtInSPsList())
