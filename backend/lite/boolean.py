from psp import PSP

class NotOutputPSP(PSP):
  def simulate(self,args): return not args.operandValues[0]
