from psp import PSP, ESRRefOutputPSP
from sp import SP
from env import Env
from request import Request,ESR


class MakeMSPOutputPSP(PSP):
  def simulate(self,args):
    sharedOperatorNode = args.operandNodes[0]
    return SP(MSPRequestPSP(sharedOperatorNode),ESRRefOutputPSP())

  def description(self,name):
    return "(%s <SP a b>) -> <SP a b>\n  Returns the stochastically memoized version of the input SP." % name

class MSPRequestPSP(PSP):
  def __init__(self,sharedOperatorNode): self.sharedOperatorNode = sharedOperatorNode
  def simulate(self,args): 
    id = str(args.operandValues)
    exp = ["memoizedSP"] + [["quote",val] for val in args.operandValues]
    env = Env(None,["memoizedSP"],[self.sharedOperatorNode])
    return Request([ESR(id,exp,env)])
