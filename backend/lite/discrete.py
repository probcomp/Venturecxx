import random
from utils import sampleCategorical, normalizeList
from psp import PSP

class BernoulliOutputPSP(PSP):
  def simulate(self,args): return random.random() < args.operandValues[0]
    
  def logDensity(self,val,args):
    p = args.operandValues[0]
    if val: return math.log(p)
    else: return math.log(1 - p)

  def canAbsorb(self): return True

class CategoricalOutputPSP(PSP):
  def simulate(self,args): 
    ps = normalizeList(args.operandValues)
    return sampleCategorical(ps)

  def logDensity(self,val,args):
    ps = normalizeList(args.operandValues)
    return math.log(ps[val])

  def canAbsorb(self): return True

