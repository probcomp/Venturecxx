# Copyright (c) 2014 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

import math
from abc import ABCMeta, abstractmethod
from collections import OrderedDict
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
      return regenAndAttach(Particle(trace),scaffold,False,OmegaDB(),OrderedDict())
  return f

class SliceOperator(object):
  __metaclass__ = ABCMeta

  @abstractmethod
  def findInterval(self,f,x0,logy,py_rng): pass

  @abstractmethod
  def legalProposal(self,f,x0,x1,logy,L,R): pass

  def sampleInterval(self,f,x0,logy,L,R,py_rng):
    maxIters = 10000
    it = 0
    while True:
      it += 1
      if it == maxIters: raise Exception("Cannot sample interval for slice")
      U = py_rng.random()
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

    f = makeDensityFunction(trace,scaffold,psp,pnode,
                            FixedRandomness(trace.py_rng, trace.np_rng))
    rhoLD = f(currentValue)
    logy = rhoLD + math.log(trace.py_rng.uniform(0,1))
    # print "Slicing with x0", currentValue, "w", w, "m", m
    L,R = self.findInterval(f,currentValue,logy,trace.py_rng)
    proposedValue = self.sampleInterval(f,currentValue,logy,L,R,trace.py_rng)
    xiLD = f(proposedValue)
    proposedVValue = VentureNumber(proposedValue)
    scaffold.lkernels[pnode] = DeterministicLKernel(psp,proposedVValue)
    xiWeight = regenAndAttach(trace,scaffold,False,self.rhoDB,OrderedDict())

    # Cancel out weight compensation.  From Puma's "slice.cxx":
    #  "This is subtle. We cancel out the weight compensation that we got
    #   by "forcing" x1, so that the weight is as if it had been sampled.
    #   This is because this weight is cancelled elsewhere (in the mixing
    #   over the slice)."
    return trace, (xiWeight - xiLD) - (rhoWeight - rhoLD)

  def accept(self):
    return self.scaffold.numAffectedNodes()

  def reject(self):
    detachAndExtract(self.trace,self.scaffold)
    regenAndAttach(self.trace,self.scaffold,True,self.rhoDB,OrderedDict())
    return self.scaffold.numAffectedNodes()


class StepOutSliceOperator(SliceOperator):
  def __init__(self, w, m):
    self.w = w
    self.m = m

  def name(self): return "slice sampling with stepping out"

  # "stepping out" procedure
  # See "Slice Sampling" (Neal 2000) p11 for details
  def findInterval(self,f,x0,logy,py_rng):
    U = py_rng.random()
    L = x0 - self.w * U
    R = L + self.w

    V = py_rng.random()
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
  def findInterval(self,f,x0,logy,py_rng):
    U = py_rng.random()
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
      if py_rng.random() < 0.5:
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
