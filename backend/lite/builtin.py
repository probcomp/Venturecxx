from sp import SP
from psp import NullRequestPSP

import discrete
import continuous
import number
import csp

def builtInValues(): return { "true" : True, "false" : False }

def builtInSPs():
  return { "+" : SP(NullRequestPSP,number.PlusOutputPSP),
           "-" : SP(NullRequestPSP,number.MinusOutputPSP),
           "bernoulli" : SP(NullRequestPSP,discrete.BernoulliOutputPSP),
           "normal" : SP(NullRequestPSP,continuous.NormalOutputPSP),
           "make_csp" : SP(NullRequestPSP,csp.MakeCSPOutputPSP),
  }



