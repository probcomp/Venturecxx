from psp import PSP

class BranchRequestPSP(PSP):
  def simulate(self,args): 
    if args.operandValues[0]: expIndex = 1
    else: expIndex = 2

    exp = args.operandValues[expIndex]
    return ([(args.node,exp,args.env)],[])
