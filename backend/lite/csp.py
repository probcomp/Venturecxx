from psp import PSP, ESRRefOutputPSP
from sp import SP
from env import Env
from request import Request,ESR

class CSPRequestPSP(PSP):
  def __init__(self,ids,exp,env):
    self.ids = ids
    self.exp = exp
    self.env = env

  def simulate(self,args):
    assert len(self.ids) == len(args.operandNodes)
    extendedEnv = Env(self.env,self.ids,args.operandNodes)
    return Request([ESR(args.node,self.exp,extendedEnv)])

  def canAbsorb(self): return True

class MakeCSPOutputPSP(PSP):
  def simulate(self,args):
    (ids,exp) = args.operandValues[0:3]
    return SP(CSPRequestPSP(ids,exp,args.env),ESRRefOutputPSP())

  def description(self,name):
    return "%s is used internally in the implementation of compound procedures" % name
