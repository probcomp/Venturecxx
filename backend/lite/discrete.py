import random
import math
import scipy
import scipy.special
import numpy.random as npr
from utils import simulateCategorical, logDensityCategorical, simulateDirichlet, logDensityDirichlet
from psp import PSP, NullRequestPSP, RandomPSP
from sp import SP
from lkernel import LKernel


class BernoulliOutputPSP(RandomPSP):
  def simulate(self,args):
    p = args.operandValues[0] if args.operandValues else 0.5
    return random.random() < p
    
  def logDensity(self,val,args):
    p = args.operandValues[0] if args.operandValues else 0.5
    if val: return math.log(p)
    else: return math.log(1 - p)

  def enumerateValues(self,args):
    p = args.operandValues[0] if args.operandValues else 0.5
    if p == 1: return [True]
    elif p == 0: return [False]
    else: return [True,False]

class CategoricalOutputPSP(RandomPSP):
  # (categorical ps outputs)
  def simulate(self,args): 
    return simulateCategorical(*args.operandValues)

  def logDensity(self,val,args):
    return logDensityCategorical(val,*args.operandValues)

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

################### Symmetric Dirichlet

class SymmetricDirichletOutputPSP(RandomPSP):

  def simulate(self,args):
    (alpha,n) = (float(args.operandValues[0]),int(args.operandValues[1]))
    return simulateDirichlet([alpha for i in range(n)])
    
  def logDensity(self,val,args):
    (alpha,n) = (float(args.operandValues[0]),int(args.operandValues[1]))
    return logDensityDirichlet(val,[alpha for i in range(n)])


class DirMultSP(SP):
  def __init__(self,requestPSP,outputPSP,n):
    super(DirMultSP,self).__init__(requestPSP,outputPSP)
    self.n = n

  def constructSPAux(self): return [0.0 for i in range(self.n)]


### Collapsed SymDirMult

class MakerCSymDirMultOutputPSP(PSP):
  def simulate(self,args):
    (alpha,n) = (float(args.operandValues[0]),int(args.operandValues[1]))
    os = args.operandValues[2] if len(args.operandValues) > 2 else range(n)
    return DirMultSP(NullRequestPSP(),CSymDirMultOutputPSP(alpha,n,os),n)

  def childrenCanAAA(self): return True

class CSymDirMultOutputPSP(RandomPSP):
  def __init__(self,alpha,n,os):
    self.alpha = alpha
    self.n = n
    self.os = os

  def simulate(self,args):
    counts = [count + self.alpha for count in args.spaux]
    return simulateCategorical(counts,self.os)
      
  def logDensity(self,val,args):
    counts = [count + self.alpha for count in args.spaux]
    return logDensityCategorical(val,counts,self.os)

  def incorporate(self,val,args):
    index = self.os.index(val)
    args.spaux[index] += 1
    
  def remove(self,val,args):
    index = self.os.index(val)
    args.spaux[index] -= 1
        
  def logDensityOfCounts(self,aux):
    N = sum(aux)
    A = self.alpha * self.n

    term1 = scipy.special.gammaln(A) - scipy.special.gammaln(N + A)
    galpha = scipy.special.gammaln(self.alpha)
    term2 = sum([scipy.special.gammaln(self.alpha + aux[index]) - galpha for index in range(self.n)])
    return term1 + term2

#### Uncollapsed SymDirMult

class MakerUSymDirMultOutputPSP(RandomPSP):
  def childrenCanAAA(self): return True
  def getAAALKernel(self): return USymDirMultAAALKernel()

  def simulate(self,args):
    (alpha,n) = (float(args.operandValues[0]),int(args.operandValues[1]))
    os = args.operandValues[2] if len(args.operandValues) > 2 else range(n)
    theta = npr.dirichlet([alpha for i in range(n)])
    return DirMultSP(NullRequestPSP(),USymDirMultOutputPSP(theta,os),n)

  def logDensity(self,value,args):
    (alpha,n) = (float(args.operandValues[0]),int(args.operandValues[1]))
    os = args.operandValues[2] if len(args.operandValues) > 2 else range(n)
    assert isinstance(value,DirMultSP)
    assert isinstance(value.outputPSP,USymDirMultOutputPSP)
    return logDensityDirichlet(value.outputPSP.theta,[alpha for i in range(n)])

class USymDirMultAAALKernel(LKernel):
  def simulate(self,trace,oldValue,args):
    (alpha,n) = (float(args.operandValues[0]),int(args.operandValues[1]))
    os = args.operandValues[2] if len(args.operandValues) > 2 else range(n)
    counts = [count + alpha for count in args.madeSPAux]
    newTheta = npr.dirichlet(counts)
    return DirMultSP(NullRequestPSP(),USymDirMultOutputPSP(newTheta,os),n)

class USymDirMultOutputPSP(RandomPSP):
  def __init__(self,theta,os):
    self.theta = theta
    self.os = os

  def simulate(self,args): return simulateCategorical(self.theta,self.os)

  def logDensity(self,val,args): return logDensityCategorical(val,self.theta,self.os)

  def incorporate(self,val,args):
    index = self.os.index(val)
    args.spaux[index] += 1
    
  def remove(self,val,args):
    index = self.os.index(val)
    args.spaux[index] -= 1

################### (Not-necessarily-symmetric) Dirichlet-Multinomial

class DirichletOutputPSP(RandomPSP):

  def simulate(self,args):
    alpha = args.operandValues[0]
    return simulateDirichlet(alpha)
    
  def logDensity(self,val,args):
    alpha = args.operandValues[0]
    return logDensityDirichlet(val,alpha)

### Collapsed Dirichlet-Multinomial

class MakerCDirMultOutputPSP(PSP):
  def simulate(self,args):
    alpha = args.operandValues[0]
    os = args.operandValues[1] if len(args.operandValues) > 1 else range(len(alpha))
    return DirMultSP(NullRequestPSP(),CDirMultOutputPSP(alpha,os),len(alpha))

  def childrenCanAAA(self): return True


class CDirMultOutputPSP(RandomPSP):
  def __init__(self,alpha,os):
    self.alpha = alpha
    self.os = os

  def simulate(self,args):
    counts = [count + alpha for (count,alpha) in zip(args.spaux,self.alpha)]
    return simulateCategorical(counts,self.os)
      
  def logDensity(self,val,args):
    counts = [count + alpha for (count,alpha) in zip(args.spaux,self.alpha)]
    return logDensityCategorical(val,counts,self.os)

  def incorporate(self,val,args):
    index = self.os.index(val)
    args.spaux[index] += 1
    
  def remove(self,val,args):
    index = self.os.index(val)
    args.spaux[index] -= 1
        
  def logDensityOfCounts(self,aux):
    N = sum(aux)
    A = sum(self.alpha)

    term1 = scipy.special.gammaln(A) - scipy.special.gammaln(N + A)
    term2 = sum([scipy.special.gammaln(alpha + count) - scipy.special.gammaln(alpha) for (alpha,count) in zip(self.alpha,aux)])
    return term1 + term2

#### Uncollapsed DirMult

class MakerUDirMultOutputPSP(RandomPSP):
  def childrenCanAAA(self): return True
  def getAAALKernel(self): return UDirMultAAALKernel()

  def simulate(self,args):
    alpha = args.operandValues[0]
    n = len(alpha)
    os = args.operandValues[1] if len(args.operandValues) > 1 else range(n)
    theta = npr.dirichlet(alpha)
    return DirMultSP(NullRequestPSP(),UDirMultOutputPSP(theta,os),n)

  def logDensity(self,value,args):
    alpha = args.operandValues[0]
    os = args.operandValues[1] if len(args.operandValues) > 1 else range(len(alpha))

    assert isinstance(value,DirMultSP)
    assert isinstance(value.outputPSP,UDirMultOutputPSP)
    return logDensityDirichlet(value.outputPSP.theta,alpha)

class UDirMultAAALKernel(LKernel):
  def simulate(self,trace,oldValue,args):
    alpha = args.operandValues[0]
    os = args.operandValues[1] if len(args.operandValues) > 1 else range(len(alpha))
    counts = [count + a for (count,a) in zip(args.madeSPAux,alpha)]
    newTheta = npr.dirichlet(counts)
    return DirMultSP(NullRequestPSP(),UDirMultOutputPSP(newTheta,os),len(alpha))

class UDirMultOutputPSP(RandomPSP):
  def __init__(self,theta,os):
    self.theta = theta
    self.os = os

  def simulate(self,args): return simulateCategorical(self.theta,self.os)

  def logDensity(self,val,args): return logDensityCategorical(val,self.theta,self.os)

  def incorporate(self,val,args):
    index = self.os.index(val)
    args.spaux[index] += 1
    
  def remove(self,val,args):
    index = self.os.index(val)
    args.spaux[index] -= 1
