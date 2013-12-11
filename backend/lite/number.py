from psp import PSP

class PlusOutputPSP(PSP):
  def simulate(self,args): return sum(args.operandValues)

class MinusOutputPSP(PSP):
  def simulate(self,args): return args.operandValues[0] - args.operandValues[1]




