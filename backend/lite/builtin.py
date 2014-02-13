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

# The types in the value module are generated programmatically, so
# pylint doesn't find out about them.
# pylint: disable=no-member

def builtInValues():
  return { "true" : v.VentureBool(True), "false" : v.VentureBool(False) }

def deterministic_psp(f):
  class DeterministicPSP(PSP):
    def simulate(self,args):
      return f(*args.operandValues)
    def description(self,name):
      return "deterministic %s" % name
  return DeterministicPSP()

def deterministic(f):
  return VentureSP(NullRequestPSP(), deterministic_psp(f))

def deterministic_typed(f, args_types, return_type, variadic=False):
  return VentureSP(NullRequestPSP(), TypedPSP(args_types, return_type, deterministic_psp(f), variadic))

def binaryNum(f):
  return deterministic_typed(f, [v.NumberType(), v.NumberType()], v.NumberType())

def unaryNum(f):
  return deterministic_typed(f, [v.NumberType()], v.NumberType())

def naryNum(f):
  return deterministic_typed(f, [v.NumberType()], v.NumberType(), True)

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

           [ "list", deterministic(v.pythonListToVentureList) ],
           [ "pair", deterministic(v.VenturePair) ],
           [ "is_pair", type_test(v.VenturePair) ],
           [ "first", deterministic_typed(lambda p: p[0], [v.PairType()], v.AnyType()) ],
           [ "rest", deterministic_typed(lambda p: p[1], [v.PairType()], v.AnyType()) ],
           [ "second", deterministic_typed(lambda p: p[1].first, [v.PairType()], v.AnyType()) ],

           [ "map_list",VentureSP(dstructures.MapListRequestPSP(),dstructures.MapListOutputPSP()) ],

           [ "array", deterministic(lambda *args: v.VentureArray(np.array(args))) ],
           [ "is_array", type_test(v.VentureArray) ],
           [ "dict", VentureSP(NullRequestPSP(),dstructures.DictOutputPSP()) ],
           [ "is_dict", type_test(v.VentureDict) ],
           [ "matrix", deterministic(lambda rows: v.VentureMatrix(np.mat([row.asPythonList() for row in rows.asPythonList()]))) ], # TODO Put in the description that the input is a list of the rows of the matrix
           [ "is_matrix", type_test(v.VentureMatrix) ],
           [ "simplex", deterministic_typed(lambda *nums: np.array(nums), [v.NumberType()], v.SimplexType(), variadic=True) ],
           [ "is_simplex", type_test(v.VentureSimplex) ],

           [ "lookup", deterministic(lambda xs, x: xs.lookup(x)) ],
           [ "contains", deterministic(lambda xs, x: v.VentureBool(xs.contains(x))) ],
           [ "size", deterministic(lambda xs: v.VentureNumber(xs.size())) ],

           [ "branch", VentureSP(conditionals.BranchRequestPSP(),ESRRefOutputPSP()) ],
           [ "biplex", deterministic_typed(lambda p, c, a: c if p else a, [v.BoolType(), v.AnyType(), v.AnyType()], v.AnyType())],
           [ "make_csp", VentureSP(NullRequestPSP(),csp.MakeCSPOutputPSP()) ],

           [ "eval",VentureSP(eval_sps.EvalRequestPSP(),ESRRefOutputPSP()) ],
           [ "get_current_environment",VentureSP(NullRequestPSP(),eval_sps.GetCurrentEnvOutputPSP()) ],
           [ "get_empty_environment",VentureSP(NullRequestPSP(),eval_sps.GetEmptyEnvOutputPSP()) ],
           [ "extend_environment",VentureSP(NullRequestPSP(),eval_sps.ExtendEnvOutputPSP()) ],

           [ "mem",VentureSP(NullRequestPSP(),msp.MakeMSPOutputPSP()) ],

           [ "scope_include",VentureSP(NullRequestPSP(),scope.ScopeIncludeOutputPSP()) ],

           [ "binomial", VentureSP(NullRequestPSP(),discrete.BinomialOutputPSP()) ],           
           [ "flip",VentureSP(NullRequestPSP(),discrete.BernoulliOutputPSP()) ],
           [ "bernoulli",VentureSP(NullRequestPSP(),discrete.BernoulliOutputPSP()) ],
           [ "categorical",VentureSP(NullRequestPSP(),discrete.CategoricalOutputPSP()) ],

           [ "normal",VentureSP(NullRequestPSP(),continuous.NormalOutputPSP()) ],
           [ "uniform_continuous",VentureSP(NullRequestPSP(),continuous.UniformOutputPSP()) ],
           [ "beta",VentureSP(NullRequestPSP(),continuous.BetaOutputPSP()) ],
           [ "gamma",VentureSP(NullRequestPSP(),continuous.GammaOutputPSP()) ],
           [ "student_t",VentureSP(NullRequestPSP(),continuous.StudentTOutputPSP()) ],

           [ "dirichlet",VentureSP(NullRequestPSP(),discrete.DirichletOutputPSP()) ],
           [ "symmetric_dirichlet",VentureSP(NullRequestPSP(),discrete.SymmetricDirichletOutputPSP()) ],

           [ "make_dir_mult",VentureSP(NullRequestPSP(),discrete.MakerCDirMultOutputPSP()) ],
           [ "make_uc_dir_mult",VentureSP(NullRequestPSP(),discrete.MakerUDirMultOutputPSP()) ],

           [ "make_beta_bernoulli",VentureSP(NullRequestPSP(),discrete.MakerCBetaBernoulliOutputPSP()) ],
           [ "make_uc_beta_bernoulli",VentureSP(NullRequestPSP(),discrete.MakerUBetaBernoulliOutputPSP()) ],

           [ "make_sym_dir_mult",VentureSP(NullRequestPSP(),discrete.MakerCSymDirMultOutputPSP()) ],
           [ "make_uc_sym_dir_mult",VentureSP(NullRequestPSP(),discrete.MakerUSymDirMultOutputPSP()) ],

           [ "make_crp",VentureSP(NullRequestPSP(),crp.MakeCRPOutputPSP()) ],

           [ "make_lazy_hmm",VentureSP(NullRequestPSP(),hmm.MakeUncollapsedHMMOutputPSP()) ],
  ]

def builtInSPs():
  return dict(builtInSPsList())
