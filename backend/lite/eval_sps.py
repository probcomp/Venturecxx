from psp import PSP, ESRRefOutputPSP
from sp import SP
from env import Env
from request import Request,ESR

class EvalRequestPSP(PSP):
  def simulate(self,args):
    exp,env = args.operandValues
    return Request([ESR(args.node,exp,env)])

class GetCurrentEnvOutputPSP(PSP):
  def simulate(self,args): return args.env

class GetEmptyEnvOutputPSP(PSP):
  def simulate(self,args): return Env()

class ExtendEnvOutputPSP(PSP):
  def simulate(self,args): 
    env,sym = args.operandValues[0:2]
    node = args.operandNodes[2]
    return Env(env,[sym],[node])

    
