import random
import math
from omegadb import OmegaDB
from regen import regenAndAttach
from detach import detachAndExtract
from lkernel import DeterministicLKernel
from utils import FixedRandomness
from value import VentureNumber

# "stepping out" procedure
# See "Slice Sampling" (Neal 2000) p11 for details
def findInterval(f,x0,logy,w,m):
  U = random.random()
  L = x0 - w * U
  R = L + w

  V = random.random()
  J = math.floor(m * V)
  K = (m - 1) - J

  maxIters = 10000

  iterJ = 0
  while J > 0:
    iterJ += 1
    if iterJ == maxIters: raise Exception("Cannot find interval for slice")
    fl = f(L)
    # print "Expanding down from L", L, "f(L)", fl, "logy", logy
    if logy >= fl: break
    if math.isnan(fl): break
    L = L - w
    J = J - 1

  iterK = 0
  while K > 0:
    iterK += 1
    if iterK == maxIters: raise Exception("Cannot find interval for slice")
    fr = f(R)
    # print "Expanding up from R", R, "f(R)", fr, "logy", logy
    if logy >= fr: break
    if math.isnan(fr): break
    R = R + w
    K = K - 1

  return L,R

def sampleInterval(f,x0,logy,L,R):
  maxIters = 10000
  it = 0
  while True:
    it += 1
    if it == maxIters: raise Exception("Cannot sample interval for slice")
    U = random.random()
    x1 = L + U * (R - L)
    fx1 = f(x1)
    # print "Slicing at x1", x1, "f(x1)", fx1, "logy", logy, "L", L, "R", R
    if logy <= fx1: return x1
    if x1 < x0: L = x1
    else: R = x1

def makeDensityFunction(trace,scaffold,psp,pnode,fixed_randomness):
  from particle import Particle
  def f(x):
    with fixed_randomness:
      scaffold.lkernels[pnode] = DeterministicLKernel(psp,VentureNumber(x))
      # The particle is a way to regen without clobbering the underlying trace
      # TODO Do repeated regens along the same scaffold actually work?
      return regenAndAttach(Particle(trace),scaffold,False,OmegaDB(),{})
  return f

class SliceOperator(object):

  def __init__(self, w, m):
    self.w = w
    self.m = m

  def propose(self,trace,scaffold):
    self.trace = trace
    self.scaffold = scaffold

    pnode = scaffold.getPNode()
    psp = trace.pspAt(pnode)
    currentVValue = trace.valueAt(pnode)
    currentValue = currentVValue.getNumber()
    scaffold.lkernels[pnode] = DeterministicLKernel(psp,currentVValue)

    rhoWeight,self.rhoDB = detachAndExtract(trace,scaffold)

    f = makeDensityFunction(trace,scaffold,psp,pnode,FixedRandomness())
    logy = f(currentValue) + math.log(random.uniform(0,1))
    # print "Slicing with x0", currentValue, "w", w, "m", m
    L,R = findInterval(f,currentValue,logy,self.w,self.m)
    proposedValue = sampleInterval(f,currentValue,logy,L,R)
    proposedVValue = VentureNumber(proposedValue)
    scaffold.lkernels[pnode] = DeterministicLKernel(psp,proposedVValue)

    xiWeight = regenAndAttach(trace,scaffold,False,self.rhoDB,{})
    return trace,xiWeight - rhoWeight

  def accept(self): pass
  def reject(self):
    detachAndExtract(self.trace,self.scaffold)
    regenAndAttach(self.trace,self.scaffold,True,self.rhoDB,{})
  def name(self): return "slice sampling"