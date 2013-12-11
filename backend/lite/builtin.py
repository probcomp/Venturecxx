from sp import SP
from psp import NullRequestPSP, ESRRefOutputPSP

import discrete
import continuous
import number
import csp
import msp
import conditionals

def builtInValues(): return { "true" : True, "false" : False }

def builtInSPs():
  return { "plus" : SP(NullRequestPSP(),number.PlusOutputPSP()),
           "minus" : SP(NullRequestPSP(),number.MinusOutputPSP()),
           "bernoulli" : SP(NullRequestPSP(),discrete.BernoulliOutputPSP()),
           "normal" : SP(NullRequestPSP(),continuous.NormalOutputPSP()),
           "branch" : SP(conditionals.BranchRequestPSP(),ESRRefOutputPSP()),
           "make_csp" : SP(NullRequestPSP(),csp.MakeCSPOutputPSP()),
           "make_msp" : SP(NullRequestPSP(),msp.MakeMSPOutputPSP()),
  }



