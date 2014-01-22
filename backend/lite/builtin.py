import math

from sp import SP
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

def builtInValues(): return { "true" : True, "false" : False }

def deterministic(f):
  class DeterministicPSP(PSP):
    def simulate(self,args):
      print args
      return f(*args.operandValues)
  return SP(NullRequestPSP(), DeterministicPSP())

def builtInSPs():
  return { "plus" :  deterministic(lambda *args: sum(args)),
           "minus" : deterministic(lambda x,y: x - y),
           "times" : deterministic(lambda *args: reduce(lambda x,y: x * y,args,1)),
           "div" :   deterministic(lambda x,y: x / y),
           "eq" :    deterministic(lambda x,y: x == y),
           "gt" :    deterministic(lambda x,y: x < y),
           "lt" :    deterministic(lambda x,y: x > y),
           # Only makes sense with VentureAtom/VentureNumber distinction
           "real" :  deterministic(lambda x:x),

           "sin" : deterministic(math.sin),
           "cos" : deterministic(math.cos),
           "tan" : deterministic(math.tan),
           "hypot" : deterministic(math.hypot),
           "exp" : deterministic(math.exp),
           "log" : deterministic(math.log),
           "pow" : deterministic(math.pow),
           "sqrt" : deterministic(math.sqrt),

           "not" : deterministic(lambda x: not x),

           "simplex" : SP(NullRequestPSP(),dstructures.SimplexOutputPSP()),

           "array" : SP(NullRequestPSP(),dstructures.ArrayOutputPSP()),
           "lookup" : SP(NullRequestPSP(),dstructures.LookupOutputPSP()),
           "contains" : SP(NullRequestPSP(),dstructures.ContainsOutputPSP()),
           "dict" : SP(NullRequestPSP(),dstructures.DictOutputPSP()),

           "pair" : SP(NullRequestPSP(),dstructures.PairOutputPSP()),
           "list" : SP(NullRequestPSP(),dstructures.ListOutputPSP()),
           # Fake compatibility with CXX
           "make_vector" : SP(NullRequestPSP(),dstructures.ListOutputPSP()),
           "is_pair" : SP(NullRequestPSP(),dstructures.IsPairOutputPSP()),
           "list_ref" : SP(NullRequestPSP(),dstructures.ListRefOutputPSP()),
           "first" : SP(NullRequestPSP(),dstructures.FirstListOutputPSP()),
           "rest" : SP(NullRequestPSP(),dstructures.RestListOutputPSP()),

           "flip" : SP(NullRequestPSP(),discrete.BernoulliOutputPSP()),
           "bernoulli" : SP(NullRequestPSP(),discrete.BernoulliOutputPSP()),
           "categorical" : SP(NullRequestPSP(),discrete.CategoricalOutputPSP()),

           "normal" : SP(NullRequestPSP(),continuous.NormalOutputPSP()),

           "uniform_continuous" : SP(NullRequestPSP(),continuous.UniformOutputPSP()),
           "beta" : SP(NullRequestPSP(),continuous.BetaOutputPSP()),

           "gamma" : SP(NullRequestPSP(),continuous.GammaOutputPSP()),
           "student_t" : SP(NullRequestPSP(),continuous.StudentTOutputPSP()),

           "branch" : SP(conditionals.BranchRequestPSP(),ESRRefOutputPSP()),
           "biplex" : SP(NullRequestPSP(),conditionals.BiplexOutputPSP()),

           "make_csp" : SP(NullRequestPSP(),csp.MakeCSPOutputPSP()),

           "mem" : SP(NullRequestPSP(),msp.MakeMSPOutputPSP()),

           "make_beta_bernoulli" : SP(NullRequestPSP(),discrete.MakerCBetaBernoulliOutputPSP()),
           "make_uc_beta_bernoulli" : SP(NullRequestPSP(),discrete.MakerUBetaBernoulliOutputPSP()),

           "make_sym_dir_mult" : SP(NullRequestPSP(),discrete.MakerCSymDirMultOutputPSP()),
           "make_uc_sym_dir_mult" : SP(NullRequestPSP(),discrete.MakerUSymDirMultOutputPSP()),

           "make_dir_mult" : SP(NullRequestPSP(),discrete.MakerCDirMultOutputPSP()),
           "make_uc_dir_mult" : SP(NullRequestPSP(),discrete.MakerUDirMultOutputPSP()),

           "dirichlet" : SP(NullRequestPSP(),discrete.DirichletOutputPSP()),
           "symmetric_dirichlet" : SP(NullRequestPSP(),discrete.SymmetricDirichletOutputPSP()),

           "make_crp" : SP(NullRequestPSP(),crp.MakeCRPOutputPSP()),

           "make_lazy_hmm" : SP(NullRequestPSP(),hmm.MakeUncollapsedHMMOutputPSP()),

           "scope_include" : SP(NullRequestPSP(),scope.ScopeIncludeOutputPSP()),
  }



