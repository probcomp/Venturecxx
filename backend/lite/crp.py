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

from copy import deepcopy
import math

from scipy.special import digamma, gammaln

from venture.lite.psp import DeterministicMakerAAAPSP
from venture.lite.psp import NullRequestPSP
from venture.lite.psp import RandomPSP
from venture.lite.psp import TypedPSP
from venture.lite.sp import SP
from venture.lite.sp import SPAux
from venture.lite.sp import SPType
from venture.lite.sp import VentureSPRecord
from venture.lite.sp_help import typed_nr
from venture.lite.sp_registry import registerBuiltinSP
from venture.lite.utils import simulateCategorical
import venture.lite.types as t

"""
Implements the two-parameter Chinese Restaurant Process CRP(alpha, d=0) where
alpha is the concentration parameter and d is the discount parameter (which
defaults to zero, recovering the one parameter CRP). The parameters must satisfy

either
  -- d \in [0,1] and alpha > -d
or
  -- d = -k (k > 0) and alpha = Ld for L \in {1,2,...}

The current implementation does not ensure that either of these conditions, and
failing to either enter valid hyperparameters directly or assign hyperpriors
with the valid domains will results in dangerous behavior.
"""

class CRPSPAux(SPAux):
  def __init__(self):
    self.tableCounts = {}
    self.nextTable = 1
    self.freeTables = set()
    self.numTables = 0
    self.numCustomers = 0

  def copy(self):
    crp = CRPSPAux()
    crp.tableCounts = deepcopy(self.tableCounts)
    crp.nextTable = self.nextTable
    crp.freeTables = self.freeTables.copy()
    crp.numTables = self.numTables
    crp.numCustomers = self.numCustomers
    return crp

  def cts(self):
    # XXX Check that this is the correct way to return suffstats.
    return [self.tableCounts, self.numTables, self.numCustomers]

class CRPSP(SP):
  def constructSPAux(self):
    return CRPSPAux()

  def show(self, spaux):
    return {
      'type' : 'crp',
      'counts': spaux.tableCounts,
    }

class MakeCRPOutputPSP(DeterministicMakerAAAPSP):
  def simulate(self, args):
    vals = args.operandValues()
    alpha = vals[0]
    d = vals[1] if len(vals) == 2 else 0
    output = TypedPSP(CRPOutputPSP(alpha, d), SPType([], t.AtomType()))
    return VentureSPRecord(CRPSP(NullRequestPSP(), output))

  def gradientOfLogDensityOfCounts(self, aux, args):
    # This function is strange because d is an optional parameter.
    # Question 1: Will args always have (alpha, d)?
    # Question 2: If not, do we return either a length one list (if only alpha)
    #   and length two list (if both alph and d)?
    # For now, just compute the graident for Case 1 (d=0).
    vals = args.operandValues()
    alpha = vals[0]
    if len(vals) == 2 and vals[1] != 0:
      raise ValueError('Gradient of CRP implemented only for one-parmaeter '
        'case.')
    [_, numTables, numCustomers] = aux.cts()
    return [numTables/alpha - (digamma(alpha + numCustomers) - digamma(alpha))]

  def description(self, name):
    return ('  %s(alpha, d) -> <SP () <number>>\n  Chinese Restaurant Process '
      'with hyperparameters alpha, and d (defaults to zero, recovering the '
      'one-parameter CRP). Returns a sampler for the table number.' % name)

class CRPOutputPSP(RandomPSP):
  def __init__(self, alpha, d):
    self.alpha = float(alpha)
    self.d = float(d)

  def simulate(self, args):
    aux = args.spaux()
    oldTables = [i for i in aux.tableCounts]
    counts = [aux.tableCounts[i] - self.d for i in oldTables] + \
        [self.alpha + (aux.numTables * self.d)]
    nextTable = aux.nextTable if len(aux.freeTables) == 0 \
        else iter(aux.freeTables).next()
    allTables = oldTables + [nextTable]
    return simulateCategorical(counts, allTables)

  def logDensity(self, table, args):
    aux = args.spaux()
    if table in aux.tableCounts:
      return math.log(aux.tableCounts[table] - self.d) - \
        math.log(self.alpha + aux.numCustomers)
    else:
      return math.log(self.alpha + (aux.numTables * self.d)) - \
        math.log(self.alpha + aux.numCustomers)

  def incorporate(self, table, args):
    aux = args.spaux()
    aux.numCustomers += 1
    if table in aux.tableCounts:
      aux.tableCounts[table] += 1
    else:
      aux.tableCounts[table] = 1
      aux.numTables += 1
      if table in aux.freeTables:
        aux.freeTables.discard(table)
      else:
        aux.nextTable = max(table+1, aux.nextTable)

  def unincorporate(self, table, args):
    aux = args.spaux()
    aux.numCustomers -= 1
    aux.tableCounts[table] -= 1
    if aux.tableCounts[table] == 0:
      aux.numTables -= 1
      del aux.tableCounts[table]
      aux.freeTables.add(table)

  def logDensityOfCounts(self, aux):
    # For derivation see Section Chinese Restaraunt Process in
    # doc/sp-math/sp-math.tex and sources therein, use:
    #   self.alpha = \theta,
    #   self.d = \alpha
    # term1 and term2 are the log numerator, and term3 is the log denominator.
    # log( (foo+1)_{bar-1} ) in the notation of sp-math.tex turns into
    # gammaln(foo+bar) - gammaln(foo+1)
    # TODO No doubt there is a numerically better way to compute this quantity.
    term1 = sum(math.log(self.alpha + i*self.d)
      for i in xrange(1, aux.numTables))
    term2 = sum(gammaln(aux.tableCounts[t]-self.d) - gammaln(1-self.d)
      for t in aux.tableCounts)
    term3 = gammaln(self.alpha + max(aux.numCustomers, 1)) - \
        gammaln(self.alpha+1)
    return term1 + term2 - term3

  def enumerateValues(self, args):
    aux = args.spaux()
    oldTables = [i for i in aux.tableCounts]
    return oldTables + [aux.nextTable]

registerBuiltinSP('make_crp', typed_nr(MakeCRPOutputPSP(),
    [t.NumberType(),t.NumberType()], SPType([], t.AtomType()), min_req_args=1))
