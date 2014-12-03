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

  def description(self, name):
    return '(%s epsilon x) -> x\n  Identity function that can be observed to induce noisy equality between input and output. log(epsilon) is the penalty for mismatch.' % name

