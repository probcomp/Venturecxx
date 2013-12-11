import sp
import psp

import discrete
import continuous
import number
import csp

def builtInValues(): return { "true" : True, "false" : False }

def builtInSPs():
  return { "+" : SP(NullRequestPSP,PlusOutputPSP),
           "-" : SP(NullRequestPSP,MinusOutputPSP),
           "bernoulli" : SP(NullRequestPSP,BernoulliOutputPSP),
           "normal" : SP(NullRequestPSP,NormalOutputPSP),
           "branch" : SP(BranchRequestPSP,ESRReferencePSP),
           "make_csp" : SP(NullRequestPSP,MakeCSPOutputPSP),
  }



