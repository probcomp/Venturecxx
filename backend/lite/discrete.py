import random
from psp import PSP

class BernoulliOutputPSP(PSP):
  def simulate(self,args): return random.random() < args.operandValues[0]
    
  def logDensity(self,val,args):
    p = args.operandValues[0]
    if val: return math.log(p)
    else: return math.log(1 - p)

  def canAbsorb(self): return True

