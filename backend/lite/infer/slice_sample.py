import random
import math
from abc import ABCMeta, abstractmethod
from ..omegadb import OmegaDB
from ..regen import regenAndAttach
from ..detach import detachAndExtract
from ..lkernel import DeterministicLKernel
from ..utils import FixedRandomness
from ..value import VentureNumber

def makeDensityFunction(trace,scaffold,psp,pnode,fixed_randomness):
  from ..particle import Particle
  def f(x):
    with fixed_randomness:
      scaffold.lkernels[pnode] = DeterministicLKernel(psp,VentureNumber(x))
      # The particle is a way to regen without clobbering the underlying trace
      # TODO Do repeated regens along the same scaffold actually work?
      return regenAndAttach(Particle(trace),scaffold,False,OmegaDB(),{})
  return f

class SliceOperator(object):
  __metaclass__ = ABCMeta

  @abstractmethod
  def findInterval(self,f,x0,logy): pass

  @abstractmethod
  def legalProposal(self,f,x0,x1,logy,L,R): pass

  def sampleInterval(self,f,x0,logy,L,R):
    maxIters = 10000
    it = 0
    while True:
      it += 1
      if it == maxIters: raise Exception("Cannot sample interval for slice")
      U = random.random()
      x1 = L + U * (R - L)
      fx1 = f(x1)
      # print "Slicing at x1", x1, "f(x1)", fx1, "logy", logy, "L", L, "R", R
      if (logy <= fx1) and self.legalProposal(f,x0,x1,logy,L,R): return x1
      if x1 < x0: L = x1
      else: R = x1

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
    L,R = self.findInterval(f,currentValue,logy)
    proposedValue = self.sampleInterval(f,currentValue,logy,L,R)
    proposedVValue = VentureNumber(proposedValue)
    scaffold.lkernels[pnode] = DeterministicLKernel(psp,proposedVValue)

    xiWeight = regenAndAttach(trace,scaffold,False,self.rhoDB,{})
    return trace,xiWeight - rhoWeight

  def accept(self): pass
  def reject(self):
    detachAndExtract(self.trace,self.scaffold)
    regenAndAttach(self.trace,self.scaffold,True,self.rhoDB,{})


class StepOutSliceOperator(SliceOperator):
  def __init__(self, w, m):
    self.w = w
    self.m = m

  def name(self): return "slice sampling with stepping out"

  # "stepping out" procedure
  # See "Slice Sampling" (Neal 2000) p11 for details
  def findInterval(self,f,x0,logy):
    U = random.random()
    L = x0 - self.w * U
    R = L + self.w

    V = random.random()
    J = math.floor(self.m * V)
    K = (self.m - 1) - J

    maxIters = 10000

    iterJ = 0
    while J > 0:
      iterJ += 1
      if iterJ == maxIters: raise Exception("Cannot find interval for slice")
      fl = f(L)
      # print "Expanding down from L", L, "f(L)", fl, "logy", logy
      if logy >= fl: break
      if math.isnan(fl): break
      L = L - self.w
      J = J - 1

    iterK = 0
    while K > 0:
      iterK += 1
      if iterK == maxIters: raise Exception("Cannot find interval for slice")
      fr = f(R)
      # print "Expanding up from R", R, "f(R)", fr, "logy", logy
      if logy >= fr: break
      if math.isnan(fr): break
      R = R + self.w
      K = K - 1

    return L,R

  def legalProposal(self,f,x0,x1,logy,L,R): return True


class DoublingSliceOperator(SliceOperator):
  def __init__(self, w, p):
    self.w = w
    self.p = p

  def name(self): return "slice sampling with doubling"

  # "doubling" procedure; p11 of Neal
  def findInterval(self,f,x0,logy):
    U = random.random()
    L = x0 - self.w * U
    R = L + self.w
    K = self.p
    maxIters = 10000
    iterK = 0
    fl = f(L)
    fr = f(R)
    while K > 0:
      iterK += 1
      if iterK == maxIters: raise Exception("Cannot find interval for slice")
      if (logy >= fl) and (logy >= fr): break
      if math.isnan(fl) or math.isnan(fr): break
      dist = R - L
      if random.random() < 0.5:
        L = L - dist
        fl = f(L)
      else:
        R = R + dist
        fr = f(R)
      K -= 1

    return L,R

  def legalProposal(self,f,x0,x1,logy,L,R):
    D = False
    fr = f(R)
    fl = f(L)
    while (R - L) > (1.1 * self.w):
      M = (L + R) / 2.0
      if ((x0 < M) and (x1 >= M)) or ((x0 >= M) and (x1 < M)):
        D = True
      if x1 < M:
        R = M
        fr = f(R)
      else:
        L = M
        fl = f(L)
      if D and (logy >= fl) and (logy >= fr):
        return False
    return True




