from psp import PSP
from request import Request,ESR

class BranchRequestPSP(PSP):
  def simulate(self,args): 
    if args.operandValues[0]: expIndex = 1
    else: expIndex = 2

    exp = args.operandValues[expIndex]
    return Request([ESR(args.node,exp,args.env)])
