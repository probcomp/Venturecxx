from sp import SP
from psp import NullRequestPSP, ESRRefOutputPSP

import discrete
import continuous
import number
import listsps
import csp
import msp
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
           "is_pair" : SP(NullRequestPSP(),listsps.IsPairOutputPSP()),
           "list_ref" : SP(NullRequestPSP(),listsps.ListRefOutputPSP()),
           "first" : SP(NullRequestPSP(),listsps.FirstListOutputPSP()),
           "rest" : SP(NullRequestPSP(),listsps.RestListOutputPSP()),

           "flip" : SP(NullRequestPSP(),discrete.BernoulliOutputPSP()),
           "bernoulli" : SP(NullRequestPSP(),discrete.BernoulliOutputPSP()),
           "categorical" : SP(NullRequestPSP(),discrete.CategoricalOutputPSP()),

           "normal" : SP(NullRequestPSP(),continuous.NormalOutputPSP()),

           "branch" : SP(conditionals.BranchRequestPSP(),ESRRefOutputPSP()),

           "make_csp" : SP(NullRequestPSP(),csp.MakeCSPOutputPSP()),

           "mem" : SP(NullRequestPSP(),msp.MakeMSPOutputPSP()),
  }



