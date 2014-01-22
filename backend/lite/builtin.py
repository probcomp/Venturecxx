from sp import SP
from psp import NullRequestPSP, ESRRefOutputPSP

import discrete
import continuous
import boolean
import number
import dstructures
import csp
import crp
import msp
import hmm
import conditionals
import scope

def builtInValues(): return { "true" : True, "false" : False }

def builtInSPs():
  return { "plus" : SP(NullRequestPSP(),number.PlusOutputPSP()),
           "minus" : SP(NullRequestPSP(),number.MinusOutputPSP()),
           "times" : SP(NullRequestPSP(),number.TimesOutputPSP()),
           "div" : SP(NullRequestPSP(),number.DivideOutputPSP()),
           "eq" : SP(NullRequestPSP(),number.EqualOutputPSP()),
           "gt" : SP(NullRequestPSP(),number.GreaterThanOutputPSP()),
           "lt" : SP(NullRequestPSP(),number.LessThanOutputPSP()),
           "real" : SP(NullRequestPSP(),number.RealOutputPSP()),

           "not" : SP(NullRequestPSP(),boolean.NotOutputPSP()),

           "simplex" : SP(NullRequestPSP(),dstructures.SimplexOutputPSP()),

           "array" : SP(NullRequestPSP(),dstructures.ArrayOutputPSP()),
           "lookup" : SP(NullRequestPSP(),dstructures.LookupOutputPSP()),

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



