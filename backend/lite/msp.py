from psp import DeterministicPSP, ESRRefOutputPSP
from sp import VentureSP
from env import VentureEnvironment
from request import Request,ESR


class MakeMSPOutputPSP(DeterministicPSP):
  def simulate(self,args):
    sharedOperatorNode = args.operandNodes[0]
    return VentureSP(MSPRequestPSP(sharedOperatorNode),ESRRefOutputPSP())

  def description(self,name):
    return "%s :: <SP <SP a ... -> b> -> <SP a ... -> b>>\n  Returns the stochastically memoized version of the input SP." % name

class MSPRequestPSP(DeterministicPSP):
  def __init__(self,sharedOperatorNode): self.sharedOperatorNode = sharedOperatorNode
  def simulate(self,args): 
    id = str(args.operandValues)
    exp = ["memoizedSP"] + [["quote",val] for val in args.operandValues]
    env = VentureEnvironment(None,["memoizedSP"],[self.sharedOperatorNode])
    return Request([ESR(id,exp,env)])
