from sp import SP
from psp import NullRequestPSP, ESRRefOutputPSP

import discrete
import continuous
import number
import listsps
import csp
import msp
import hmm
import conditionals

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

           "pair" : SP(NullRequestPSP(),listsps.PairOutputPSP()),
           "list" : SP(NullRequestPSP(),listsps.ListOutputPSP()),
           # Fake compatibility with CXX
           "make_vector" : SP(NullRequestPSP(),listsps.ListOutputPSP()),
           "is_pair" : SP(NullRequestPSP(),listsps.IsPairOutputPSP()),
           "list_ref" : SP(NullRequestPSP(),listsps.ListRefOutputPSP()),
           "first" : SP(NullRequestPSP(),listsps.FirstListOutputPSP()),
           "rest" : SP(NullRequestPSP(),listsps.RestListOutputPSP()),

           "flip" : SP(NullRequestPSP(),discrete.BernoulliOutputPSP()),
           "bernoulli" : SP(NullRequestPSP(),discrete.BernoulliOutputPSP()),
           "categorical" : SP(NullRequestPSP(),discrete.CategoricalOutputPSP()),

           "normal" : SP(NullRequestPSP(),continuous.NormalOutputPSP()),
           "uniform_continuous" : SP(NullRequestPSP(),continuous.UniformOutputPSP()),
           "beta" : SP(NullRequestPSP(),continuous.BetaOutputPSP()),

           "branch" : SP(conditionals.BranchRequestPSP(),ESRRefOutputPSP()),
           "biplex" : SP(NullRequestPSP(),conditionals.BiplexOutputPSP()),

           "make_csp" : SP(NullRequestPSP(),csp.MakeCSPOutputPSP()),

           "mem" : SP(NullRequestPSP(),msp.MakeMSPOutputPSP()),

           "make_beta_bernoulli" : SP(NullRequestPSP(),discrete.MakerCBetaBernoulliOutputPSP()),
           "make_ubeta_bernoulli" : SP(NullRequestPSP(),discrete.MakerUBetaBernoulliOutputPSP()),

           "make_lazy_hmm" : SP(NullRequestPSP(),hmm.MakeUncollapsedHMMOutputPSP()),
  }



