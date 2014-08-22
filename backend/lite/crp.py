from psp import DeterministicPSP, NullRequestPSP, RandomPSP, TypedPSP
from sp import SP, VentureSPRecord, SPType
import math
import stats_utils as su
from utils import simulateCategorical
from value import AtomType # The type names are metaprogrammed pylint: disable=no-name-in-module
from copy import deepcopy

class CRPSPAux(object):
  def __init__(self):
    self.tableCounts = {}
    self.nextIndex = 1
    self.numTables = 0
    self.numCustomers = 0

  def copy(self):
    crp = CRPSPAux()
    crp.tableCounts = deepcopy(self.tableCounts)
    crp.nextIndex = self.nextIndex
    crp.numTables = self.numTables
    crp.numCustomers = self.numCustomers
    return crp

class CRPSP(SP):
  def constructSPAux(self): return CRPSPAux()
  def show(self,spaux): return spaux.tableCounts

class MakeCRPOutputPSP(DeterministicPSP):
  def simulate(self,args):
    alpha = args.operandValues[0]
    d = args.operandValues[1] if len(args.operandValues) == 2 else 0

    output = TypedPSP(CRPOutputPSP(alpha,d), SPType([], AtomType()))
    return VentureSPRecord(CRPSP(NullRequestPSP(),output))

  def childrenCanAAA(self): return True

  def description(self,name):
    return "(%s alpha) -> <SP () <number>>\n  Chinese Restaurant Process with hyperparameter alpha.  Returns a sampler for the table number." % name

class CRPOutputPSP(RandomPSP):
  def __init__(self,alpha,d):
    self.alpha = float(alpha)
    self.d = float(d)

  def simulate(self,args):
    aux = args.spaux
    old_indices = [i for i in aux.tableCounts]
    counts = [aux.tableCounts[i] - self.d for i in old_indices] + [self.alpha + (aux.numTables * self.d)]
    indices = old_indices + [aux.nextIndex]
    return simulateCategorical(counts,indices)

  def logDensity(self,index,args):
    aux = args.spaux
    if index in aux.tableCounts:
      return math.log(aux.tableCounts[index] - self.d) - math.log(self.alpha + aux.numCustomers)
    else:
      return math.log(self.alpha + (aux.numTables * self.d)) - math.log(self.alpha + aux.numCustomers)

  # def gradientOfLogDensity(self, value, args):
  #   aux = args.spaux
  #   if index in aux.tableCounts:

  def enumerateValues(self,args):
    aux = args.spaux
    old_indices = [i for i in aux.tableCounts]
    indices = old_indices + [aux.nextIndex]
    return indices

  def incorporate(self,index,args):
    aux = args.spaux
    aux.numCustomers += 1
    if index in aux.tableCounts:
      aux.tableCounts[index] += 1
    else:
      aux.tableCounts[index] = 1
      aux.numTables += 1
      aux.nextIndex = max(aux.nextIndex, index + 1)

  def unincorporate(self,index,args):
    aux = args.spaux
    aux.numCustomers -= 1
    aux.tableCounts[index] -= 1
    if aux.tableCounts[index] == 0:
      aux.numTables -= 1
      del aux.tableCounts[index]

  def logDensityOfCounts(self,aux):
    term1 = su.C.gammaln(self.alpha) - su.C.gammaln(self.alpha + aux.numCustomers)
    term2 = aux.numTables + math.log(self.alpha + (aux.numTables * self.d))
    term3 = sum([su.C.gammaln(aux.tableCounts[index] - self.d) for index in aux.tableCounts])
    return term1 + term2 + term3

  def enumerateValues(self,args):
    aux = args.spaux
    old_indices = [i for i in aux.tableCounts]
    indices = old_indices + [aux.nextIndex]
    return indices
