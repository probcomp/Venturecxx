from psp import PSP, ESRRefOutputPSP
from sp import VentureSP
from env import VentureEnvironment
from request import Request,ESR
import value as v

class CSPRequestPSP(PSP):
  def __init__(self,ids,exp,env):
    self.ids = ids
    self.exp = exp
    self.env = env

  def simulate(self,args):
    assert len(self.ids) == len(args.operandNodes)
    extendedEnv = VentureEnvironment(self.env,self.ids,args.operandNodes)
    return Request([ESR(args.node,self.exp,extendedEnv)])

  def canAbsorb(self, _trace, _appNode, _parentNode): return True

class MakeCSPOutputPSP(PSP):
  def simulate(self,args):
    ids = args.operandValues[0].getArray(v.SymbolType())
    exp = v.ExpressionType().asPython(args.operandValues[1])
    return VentureSP(CSPRequestPSP(ids,exp,args.env),ESRRefOutputPSP())

  def description(self,name):
    return "%s\n  Used internally in the implementation of compound procedures." % name
