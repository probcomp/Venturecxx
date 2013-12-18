import random
import math
import scipy
from utils import sampleCategorical, normalizeList
from psp import PSP, NullRequestPSP, RandomPSP
from sp import SP
from lkernel import LKernel

class BernoulliOutputPSP(RandomPSP):
  def simulate(self,args): return random.random() < args.operandValues[0]
    
  def logDensity(self,val,args):
    p = args.operandValues[0]
    if val: return math.log(p)
    else: return math.log(1 - p)

class CategoricalOutputPSP(RandomPSP):
  def simulate(self,args): 
    ps = normalizeList(args.operandValues)
    return sampleCategorical(ps)

  def logDensity(self,val,args):
    ps = normalizeList(args.operandValues)
    return math.log(ps[val])

#### Collapsed Beta Bernoulli

class MakerCBetaBernoulliOutputPSP(PSP):
  def childrenCanAAA(self): return True

  def simulate(self,args):
    alpha = args.operandValues[0]
    beta  = args.operandValues[1]
    return CBetaBernoulliSP(NullRequestPSP(), CBetaBernoulliOutputPSP(alpha, beta))

class CBetaBernoulliSP(SP):
  def constructSPAux(self): return [0.0,0.0]

class CBetaBernoulliOutputPSP(RandomPSP):
  def __init__(self,alpha,beta):
    self.alpha = alpha
    self.beta = beta

  def incorporate(self,value,args):
    spaux = args.spaux
    if value: # I produced true
      spaux[0] += 1
    else: # I produced false
      spaux[1] += 1

  def unincorporate(self,value,args):
    spaux = args.spaux
    if value: # I produced true
      spaux[0] -= 1
    else: # I produced false
      spaux[1] -= 1

  def simulate(self,args):
    [ctY,ctN] = args.spaux
    weight = (self.alpha + ctY) / (self.alpha + ctY + self.beta + ctN)
    return random.random() < weight

  def logDensity(self,value,args):
    [ctY,ctN] = args.spaux
    weight = (self.alpha + ctY) / (self.alpha + ctY + self.beta + ctN)
    if value == True:
      return math.log(weight)
    else:
      return math.log(1-weight)

  def logDensityOfCounts(self,aux):
    [ctY,ctN] = aux
    trues = ctY + self.alpha
    falses = ctN + self.beta
    numCombinations = scipy.misc.comb(ctY + ctN,ctY) # TODO Do this directly in log space
    numerator = scipy.special.betaln(trues,falses)
    denominator = scipy.special.betaln(self.alpha,self.beta)
    return math.log(numCombinations) + numerator - denominator

#### Uncollapsed AAA Beta Bernoulli

class MakerUBetaBernoulliOutputPSP(RandomPSP):
  def childrenCanAAA(self): return True
  def getAAALKernel(self): return UBetaBernoulliAAALKernel()

  def simulate(self,args):
    alpha = args.operandValues[0]
    beta  = args.operandValues[1]
    weight = scipy.stats.beta.rvs(alpha, beta)
    return UBetaBernoulliSP(NullRequestPSP(), UBetaBernoulliOutputPSP(weight))

  def logDensity(self,value,args):
    alpha = args.operandValues[0]
    beta  = args.operandValues[1]
    assert isinstance(value,UBetaBernoulliSP)
    coinWeight = value.outputPSP.weight
    return scipy.stats.beta.logpdf(coinWeight,alpha,beta)

class UBetaBernoulliAAALKernel(LKernel):
  def simulate(self,trace,oldValue,args):
    alpha = args.operandValues[0]
    beta  = args.operandValues[1]
    [ctY,ctN] = args.madeSPAux
    newWeight = scipy.stats.beta.rvs(alpha + ctY, beta + ctN)
    return UBetaBernoulliSP(NullRequestPSP(), UBetaBernoulliOutputPSP(newWeight))
  # Weight is zero because it's simulating from the right distribution

class UBetaBernoulliSP(SP):
  def constructSPAux(self): return [0.0,0.0]

class UBetaBernoulliOutputPSP(RandomPSP):
  def __init__(self,weight):
    self.weight = weight

  def incorporate(self,value,args):
    spaux = args.spaux
    if value: # I produced true
      spaux[0] += 1
    else: # I produced false
      spaux[1] += 1

  def unincorporate(self,value,args):
    spaux = args.spaux
    if value: # I produced true
      spaux[0] -= 1
    else: # I produced false
      spaux[1] -= 1

  def simulate(self,args): return random.random() < self.weight

  def logDensity(self,value,args):
    if value == True:
      return math.log(self.weight)
    else:
      return math.log(1-self.weight)
