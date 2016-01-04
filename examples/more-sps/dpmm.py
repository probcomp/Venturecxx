# Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
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

from collections import defaultdict
import math
import random

from venture.lite.psp import DeterministicMakerAAAPSP
from venture.lite.psp import DeterministicPSP
from venture.lite.psp import RandomPSP
from venture.lite.psp import TypedPSP
from venture.lite.request import Request
from venture.lite.sp import SP
from venture.lite.sp import SPAux
from venture.lite.sp import SPType
from venture.lite.sp import VentureSPRecord
from venture.lite.sp_help import typed_nr
from venture.lite.utils import simulateCategorical
import venture.lite.types as t

from venture.lite.discrete import BetaBernoulliSPAux
from venture.lite.crp import CRPSPAux

class DPMixtureSPAux(SPAux):
  def __init__(self):
    self.cluster_crp_aux = CRPSPAux()
    self.cluster_assignments = {} # row -> cluster
    self.cells_by_row = defaultdict(dict) # row -> (column -> value)
    self.component_bb_auxs = defaultdict(BetaBernoulliSPAux) # column x cluster -> aux

  def copy(self):
    other = DPMixtureSPAux()
    other.cluster_crp_aux = self.cluster_crp_aux.copy()
    other.cluster_assignments = self.cluster_assignments.copy()
    return other

class MakeDPMixtureOutputPSP(DeterministicMakerAAAPSP):
  def simulate(self,args):
    (cluster_crp_alpha, component_bb_alpha) = args.operandValues()
    return VentureSPRecord(DPMixtureSP(cluster_crp_alpha, component_bb_alpha))

  def description(self, _name):
    return "TODO description"

class DPMixtureSP(SP):
  def __init__(self, cluster_crp_alpha, component_bb_alpha):
    req = TypedPSP(DPMixtureRequestPSP(), SPType([t.AtomType(), t.AtomType()], t.RequestType()))
    output = TypedPSP(DPMixtureOutputPSP(component_bb_alpha), SPType([t.AtomType(), t.AtomType()], t.BoolType()))
    super(DPMixtureSP, self).__init__(req, output)
    self.cluster_crp_alpha = cluster_crp_alpha
    self.component_bb_alpha = component_bb_alpha

  def constructSPAux(self): return DPMixtureSPAux()

  # lsr: the row index
  def simulateLatents(self, args, lsr, shouldRestore, latentDB):
    aux = args.spaux()
    if lsr in aux.cluster_assignments:
      return 0

    cluster_crp_aux = aux.cluster_crp_aux
    if shouldRestore:
      index = latentDB[lsr]
    else:
      # TODO: duplicated from CRP.simulate
      old_indices = [i for i in cluster_crp_aux.tableCounts]
      counts = [cluster_crp_aux.tableCounts[i] for i in old_indices] + [self.cluster_crp_alpha]
      nextIndex = cluster_crp_aux.nextIndex if len(cluster_crp_aux.freeIndices) == 0 else cluster_crp_aux.freeIndices.__iter__().next()
      indices = old_indices + [nextIndex]
      index = simulateCategorical(counts, indices)

    # TODO: duplicated from CRP.incorporate
    cluster_crp_aux.numCustomers += 1
    if index in cluster_crp_aux.tableCounts:
      cluster_crp_aux.tableCounts[index] += 1
    else:
      cluster_crp_aux.tableCounts[index] = 1
      cluster_crp_aux.numTables += 1
      if index in cluster_crp_aux.freeIndices:
        cluster_crp_aux.freeIndices.discard(index)
      else:
        cluster_crp_aux.nextIndex = max(index+1, cluster_crp_aux.nextIndex)

    aux.cluster_assignments[lsr] = index
    return 0

  def detachLatents(self, args, lsr, latentDB):
    aux = args.spaux()
    if len(aux.cells_by_row[lsr]) > 0:
      return 0

    cluster_crp_aux = aux.cluster_crp_aux
    index = aux.cluster_assignments[lsr]

    # TODO: duplicated from CRP.unincorporate
    cluster_crp_aux.numCustomers -= 1
    cluster_crp_aux.tableCounts[index] -= 1
    if cluster_crp_aux.tableCounts[index] == 0:
      cluster_crp_aux.numTables -= 1
      del cluster_crp_aux.tableCounts[index]
      cluster_crp_aux.freeIndices.add(index)

    del aux.cluster_assignments[lsr]
    return 0

  def hasAEKernel(self): return True

  def AEInfer(self, aux):
    # Gibbs scan over the cluster assignments
    # TODO: inference control?
    cluster_crp_aux = aux.cluster_crp_aux
    for row in aux.cluster_assignments:
      index = aux.cluster_assignments[row]
      cells = aux.cells_by_row[row]

      # TODO: duplicated from CBetaBernoulli.unincorporate
      for col, value in cells.items():
        bbaux = aux.component_bb_auxs[(col, index)]
        if value: # I produced true
          bbaux.yes -= 1
        else: # I produced false
          bbaux.no -= 1

      # TODO: duplicated from CRP.unincorporate
      cluster_crp_aux.numCustomers -= 1
      cluster_crp_aux.tableCounts[index] -= 1
      if cluster_crp_aux.tableCounts[index] == 0:
        cluster_crp_aux.numTables -= 1
        del cluster_crp_aux.tableCounts[index]
        cluster_crp_aux.freeIndices.add(index)

      # TODO: partially duplicated from CRP.simulate
      old_indices = [i for i in cluster_crp_aux.tableCounts]
      counts = [cluster_crp_aux.tableCounts[i] for i in old_indices] + [self.cluster_crp_alpha]
      nextIndex = cluster_crp_aux.nextIndex if len(cluster_crp_aux.freeIndices) == 0 else cluster_crp_aux.freeIndices.__iter__().next()
      indices = old_indices + [nextIndex]

      likelihoods = []
      for z in indices:
        ll = 0
        for col, value in cells.items():
          # TODO: partially duplicated from CBetaBernoulli.logDensity
          (ctY, ctN) = aux.component_bb_auxs[(col, z)].cts()
          weight = (self.component_bb_alpha + ctY) / (self.component_bb_alpha + ctY + self.component_bb_alpha + ctN)
          if value == True:
            ll += math.log(weight)
          else:
            ll += math.log(1-weight)
        likelihoods.append(ll)

      the_max = max(likelihoods)
      conditionals = [count * math.exp(ll - the_max) for count, ll in zip(counts, likelihoods)]
      index = simulateCategorical(conditionals, indices)

      # TODO: duplicated from CRP.incorporate
      cluster_crp_aux.numCustomers += 1
      if index in cluster_crp_aux.tableCounts:
        cluster_crp_aux.tableCounts[index] += 1
      else:
        cluster_crp_aux.tableCounts[index] = 1
        cluster_crp_aux.numTables += 1
        if index in cluster_crp_aux.freeIndices:
          cluster_crp_aux.freeIndices.discard(index)
        else:
          cluster_crp_aux.nextIndex = max(index+1, cluster_crp_aux.nextIndex)

      # TODO: duplicated from CBetaBernoulli.incorporate
      for col, value in cells.items():
        bbaux = aux.component_bb_auxs[(col, index)]
        if value: # I produced true
          bbaux.yes += 1
        else: # I produced false
          bbaux.no += 1

      aux.cluster_assignments[row] = index

class DPMixtureOutputPSP(RandomPSP):
  def __init__(self, component_bb_alpha):
    self.alpha = component_bb_alpha

  def _get_component_bb_aux(self, args):
    (row, col) = args.operandValues()
    aux = args.spaux()
    z = aux.cluster_assignments[row]
    return aux.component_bb_auxs[(col, z)]

  def simulate(self, args):
    # TODO: duplicated from CBetaBernoulli.simulate
    (ctY, ctN) = self._get_component_bb_aux(args).cts()
    weight = (self.alpha + ctY) / (self.alpha + ctY + self.alpha + ctN)
    return random.random() < weight

  def logDensity(self, value, args):
    # TODO: duplicated from CBetaBernoulli.logDensity
    (ctY, ctN) = self._get_component_bb_aux(args).cts()
    weight = (self.alpha + ctY) / (self.alpha + ctY + self.alpha + ctN)
    if value == True:
      return math.log(weight)
    else:
      return math.log(1-weight)

  def incorporate(self, value, args):
    (row, col) = args.operandValues()
    cells = args.spaux().cells_by_row[row]
    # TODO: either memoize or allow for multiple observations
    assert col not in cells
    cells[col] = value

    # TODO: duplicated from CBetaBernoulli.incorporate
    spaux = self._get_component_bb_aux(args)
    if value: # I produced true
      spaux.yes += 1
    else: # I produced false
      spaux.no += 1

  def unincorporate(self, value, args):
    (row, col) = args.operandValues()
    cells = args.spaux().cells_by_row[row]
    assert cells[col] == value
    del cells[col]

    # TODO: duplicated from CBetaBernoulli.incorporate
    spaux = self._get_component_bb_aux(args)
    if value: # I produced true
      spaux.yes -= 1
    else: # I produced false
      spaux.no -= 1

class DPMixtureRequestPSP(DeterministicPSP):
  def simulate(self, args):
    (r, _) = args.operandValues()
    return Request([], [r])

def __venture_start__(ripl, *args):
  ripl.bind_foreign_sp("make_bernoulli_dpmm", typed_nr(
    MakeDPMixtureOutputPSP(),
    [t.NumberType(), t.NumberType()],
    SPType([t.AtomType(), t.AtomType()], t.BoolType())))
