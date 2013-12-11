from sp import SP
from psp import NullRequestPSP, ESRRefOutputPSP

import discrete
import continuous
import number
import csp
import conditionals

def builtInValues(): return { "true" : True, "false" : False }

def builtInSPs():
  return { "+" : SP(NullRequestPSP,number.PlusOutputPSP),
           "-" : SP(NullRequestPSP,number.MinusOutputPSP),
           "bernoulli" : SP(NullRequestPSP,discrete.BernoulliOutputPSP),
           "normal" : SP(NullRequestPSP,continuous.NormalOutputPSP),
           "branch" : SP(conditionals.BranchRequestPSP,ESRRefOutputPSP),
           "make_csp" : SP(NullRequestPSP,csp.MakeCSPOutputPSP),
  }



