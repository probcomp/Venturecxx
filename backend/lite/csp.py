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
    extendedEnv = Env(self.env,self.ids,args.operandNodes)
    return Request([ESR(args.node,self.exp,extendedEnv)])
    
class MakeCSPOutputPSP(PSP):
  def simulate(self,args):
    (ids,exp) = args.operandValues[0:3]
    return SP(CSPRequestPSP(ids,exp,args.env),ESRRefOutputPSP())
