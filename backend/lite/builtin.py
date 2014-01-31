import math

from sp import VentureSP
from psp import NullRequestPSP, ESRRefOutputPSP, PSP

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

def builtInValues(): return { "true" : True, "false" : False }

def deterministic(f):
  class DeterministicPSP(PSP):
    def simulate(self,args):
      return f(*args.operandValues)
    def description(self,name):
      return "deterministic %s" % name
  return VentureSP(NullRequestPSP(), DeterministicPSP())

def builtInSPsList():
  return [ [ "plus",  deterministic(lambda *args: sum(args)) ],
           [ "minus", deterministic(lambda x,y: x - y) ],
           [ "times", deterministic(lambda *args: reduce(lambda x,y: x * y,args,1)) ],
           [ "div",   deterministic(lambda x,y: x / y) ],
           [ "eq",    deterministic(lambda x,y: x == y) ],
           [ "gt",    deterministic(lambda x,y: x > y) ],
           [ "gte",    deterministic(lambda x,y: x >= y) ],
           [ "lt",    deterministic(lambda x,y: x < y) ],
           [ "lte",    deterministic(lambda x,y: x >= y) ],
           # Only makes sense with VentureAtom/VentureNumber distinction
           [ "real",  deterministic(lambda x:x) ],
           # Atoms appear to be represented as Python integers
           [ "atom_eq", deterministic(lambda x,y: x == y) ],

           [ "sin", deterministic(math.sin) ],
           [ "cos", deterministic(math.cos) ],
           [ "tan", deterministic(math.tan) ],
           [ "hypot", deterministic(math.hypot) ],
           [ "exp", deterministic(math.exp) ],
           [ "log", deterministic(math.log) ],
           [ "pow", deterministic(math.pow) ],
           [ "sqrt", deterministic(math.sqrt) ],

           [ "not", deterministic(lambda x: not x) ],

           # Symbols are Python strings
           [ "is_symbol", deterministic(lambda x: isinstance(x, basestring)) ],

           [ "lookup",VentureSP(NullRequestPSP(),dstructures.LookupOutputPSP()) ],
           [ "contains",VentureSP(NullRequestPSP(),dstructures.ContainsOutputPSP()) ],
           [ "size",VentureSP(NullRequestPSP(),dstructures.SizeOutputPSP()) ],

           [ "pair",VentureSP(NullRequestPSP(),dstructures.PairOutputPSP()) ],
           [ "list",VentureSP(NullRequestPSP(),dstructures.ListOutputPSP()) ],
           [ "map_list",VentureSP(dstructures.MapListRequestPSP(),dstructures.MapListOutputPSP()) ],

           # Fake compatibility with CXX
           [ "is_pair", VentureSP(NullRequestPSP(),dstructures.IsPairOutputPSP()) ],
           [ "first", VentureSP(NullRequestPSP(),dstructures.FirstListOutputPSP()) ],
           [ "second", VentureSP(NullRequestPSP(),dstructures.SecondListOutputPSP()) ],
           [ "rest", VentureSP(NullRequestPSP(),dstructures.RestListOutputPSP()) ],

           [ "array", VentureSP(NullRequestPSP(),dstructures.ArrayOutputPSP()) ],
           [ "is_array", VentureSP(NullRequestPSP(),dstructures.IsArrayOutputPSP()) ],
           [ "dict", VentureSP(NullRequestPSP(),dstructures.DictOutputPSP()) ],
           [ "matrix", VentureSP(NullRequestPSP(),dstructures.MatrixOutputPSP()) ],
           [ "simplex", VentureSP(NullRequestPSP(),dstructures.SimplexOutputPSP()) ],

           [ "branch", VentureSP(conditionals.BranchRequestPSP(),ESRRefOutputPSP()) ],
           [ "biplex", VentureSP(NullRequestPSP(),conditionals.BiplexOutputPSP()) ],
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
