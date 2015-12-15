# Copyright (c) 2013, 2014, 2015 MIT Probabilistic Computing Project.
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
from copy import copy

import numpy as np
import numpy.random as npr

from venture.lite.exception import VentureValueError
from venture.lite.psp import DeterministicPSP
from venture.lite.psp import RandomPSP
from venture.lite.psp import TypedPSP
from venture.lite.request import Request
from venture.lite.sp import SP
from venture.lite.sp import SPAux
from venture.lite.sp import SPType
from venture.lite.sp import VentureSPRecord
from venture.lite.sp_help import typed_nr
from venture.lite.sp_registry import registerBuiltinSP
import venture.lite.types as t

def npSampleVector(pVec):
  return npr.multinomial(1, pVec)
def npIndexOfOne(pVec):
  return np.where(pVec == 1)[0][0]
def npMakeDiag(colvec):
  return np.diag(np.array(colvec))
def npNormalizeVector(vec): return vec / np.sum(vec)

class HMMSPAux(SPAux):
  def __init__(self):
    super(HMMSPAux, self).__init__()
    self.xs = [] # [ x_n ],
    self.os = {} #  { n => [o_n1, ... ,o_nK] }

  def copy(self):
    ans = HMMSPAux()
    ans.xs = copy(self.xs)
    ans.os = {k:copy(v) for k, v in self.os.iteritems()}
    return ans

class MakeUncollapsedHMMOutputPSP(DeterministicPSP):
  def simulate(self, args):
    (p0, T, O) = args.operandValues()
    # Transposition for compatibility with Puma
    sp = UncollapsedHMMSP(p0, np.transpose(T), np.transpose(O))
    return VentureSPRecord(sp)

  def description(self, _name):
    return "  Discrete-state HMM of unbounded length with discrete " \
      "observations.  The inputs are the probability distribution of " \
      "the first state, the transition matrix, and the observation " \
      "matrix.  It is an error if the dimensionalities do not line up.  " \
      "Returns observations from the HMM encoded as a stochastic " \
      "procedure that takes the time step and samples a new observation " \
      "at that time step."

class UncollapsedHMMSP(SP):
  def __init__(self, p0, T, O):
    req = TypedPSP(UncollapsedHMMRequestPSP(),
                   SPType([t.CountType()], t.RequestType()))
    output = TypedPSP(UncollapsedHMMOutputPSP(O),
                      SPType([t.CountType()], t.AtomType()))
    super(UncollapsedHMMSP, self).__init__(req, output)
    self.p0 = p0
    self.T = T
    self.O = O

  def constructSPAux(self): return HMMSPAux()
  def constructLatentDB(self): return {} # { n => x_n }
  def show(self, spaux): return spaux.xs, spaux.os

  # lsr: the index of the observation needed
  def simulateLatents(self, args, lsr, shouldRestore, latentDB):
    aux = args.spaux()
    if not aux.xs:
      if shouldRestore: aux.xs.append(latentDB[0])
      else: aux.xs.append(npSampleVector(self.p0))

    for i in range(len(aux.xs), lsr + 1):
      if shouldRestore: aux.xs.append(latentDB[i])
      else: aux.xs.append(npSampleVector(np.dot(aux.xs[-1], self.T)))

    assert len(aux.xs) > lsr
    return 0

  def detachLatents(self, args, lsr, latentDB):
    aux = args.spaux()
    if len(aux.xs) == lsr + 1 and lsr not in aux.os:
      if not aux.os:
        for i in range(len(aux.xs)): latentDB[i] = aux.xs[i]
        del aux.xs[:]
      else:
        maxObservation = max(aux.os)
        for i in range(len(aux.xs) - 1, maxObservation, -1):
          latentDB[i] = aux.xs.pop()
        assert len(aux.xs) == maxObservation + 1
    return 0

  def hasAEKernel(self): return True

  def AEInfer(self, aux):
    if not aux.os: return

    # forward sampling
    fs = [self.p0]
    for i in range(1, len(aux.xs)):
      f = np.dot(fs[i-1], self.T)
      if i in aux.os:
        for o in aux.os[i]:
          f = np.dot(f, npMakeDiag(self.O[:, o]))

      fs.append(npNormalizeVector(f))

    # backwards sampling
    aux.xs[-1] = npSampleVector(fs[-1])
    for i in range(len(aux.xs) - 2, -1, -1):
      index = npIndexOfOne(aux.xs[i+1])
      T_i = npMakeDiag(self.T[:, index])
      gamma = npNormalizeVector(np.dot(fs[i], T_i))
      aux.xs[i] = npSampleVector(gamma)


class UncollapsedHMMOutputPSP(RandomPSP):

  def __init__(self, O):
    super(UncollapsedHMMOutputPSP, self).__init__()
    self.O = O

  def simulate(self, args):
    n = args.operandValues()[0]
    xs = args.spaux().xs
    if 0 <= n and n < len(xs):
      return npIndexOfOne(npSampleVector(np.dot(xs[n], self.O)))
    else:
      raise VentureValueError("Index out of bounds %s" % n)

  def logDensity(self, value, args):
    n = args.operandValues()[0]
    xs = args.spaux().xs
    assert len(xs) > n
    theta = np.dot(xs[n], self.O)
    return math.log(theta[value])

  def incorporate(self, value, args):
    n = args.operandValues()[0]
    os = args.spaux().os
    if n not in os: os[n] = []
    os[n].append(value)

  def unincorporate(self, value, args):
    n = args.operandValues()[0]
    os = args.spaux().os
    del os[n][os[n].index(value)]
    if not os[n]: del os[n]

class UncollapsedHMMRequestPSP(DeterministicPSP):
  def simulate(self, args): return Request([], [args.operandValues()[0]])

registerBuiltinSP("make_lazy_hmm", typed_nr(MakeUncollapsedHMMOutputPSP(),
    [t.SimplexType(), t.MatrixType(), t.MatrixType()],
    SPType([t.CountType()], t.AtomType())))
