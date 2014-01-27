from psp import PSP, NullRequestPSP, RandomPSP
from sp import SP
import math
import scipy.special
import scipy.stats
from utils import simulateCategorical

class CRPSPAux(object):
  def __init__(self):
    self.tableCounts = {}
    self.nextIndex = 1
    self.numTables = 0
    self.numCustomers = 0

class CRPSP(SP):
  def constructSPAux(self): return CRPSPAux()

class MakeCRPOutputPSP(PSP):
  def simulate(self,args):
    alpha = args.operandValues[0]
    return CRPSP(NullRequestPSP(),CRPOutputPSP(alpha))

  def childrenCanAAA(self): return True

  def description(self,name):
    return "(%s <alpha>) -> <SP :: () -> Number>" % name

class CRPOutputPSP(RandomPSP):
  def __init__(self,alpha): self.alpha = float(alpha)

  def simulate(self,args):
    aux = args.spaux
    old_indices = [i for i in aux.tableCounts]
    counts = [aux.tableCounts[i] for i in old_indices] + [self.alpha]
    indices = old_indices + [aux.nextIndex]
    return simulateCategorical(counts,indices)

  def logDensity(self,index,args):
    aux = args.spaux
    if index in aux.tableCounts:
      return math.log(aux.tableCounts[index]) - math.log(self.alpha + aux.numCustomers)
    else:
      return math.log(self.alpha) - math.log(self.alpha + aux.numCustomers)

  def incorporate(self,index,args):
    aux = args.spaux
    aux.numCustomers += 1
    if index in aux.tableCounts:
      aux.tableCounts[index] += 1
    else:
      aux.tableCounts[index] = 1
      aux.numTables += 1
      aux.nextIndex += 1

  def unincorporate(self,index,args):
    aux = args.spaux
    aux.numCustomers -= 1
    aux.tableCounts[index] -= 1
    if aux.tableCounts[index] == 0: 
      aux.numTables -= 1
      del aux.tableCounts[index]
        
  def logDensityOfCounts(self,aux):
    term1 = scipy.special.gammaln(self.alpha) - scipy.special.gammaln(self.alpha + aux.numCustomers)
    term2 = aux.numTables + math.log(self.alpha)
    term3 = sum([scipy.special.gammaln(aux.tableCounts[index]) for index in aux.tableCounts])
    return term1 + term2 + term3
