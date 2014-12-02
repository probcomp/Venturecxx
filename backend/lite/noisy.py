from psp import RandomPSP
from math import log

class NoisyIdentityOutputPSP(RandomPSP):
  def simulate(self, args):
    epsilon, x = args.operandValues
    return x
  
  def logDensity(self, y, args):
    epsilon, x = args.operandValues
    if y is x: return 0
    return log(epsilon)
  
  def logDensityBound(self, _y, _args):
    return 0
