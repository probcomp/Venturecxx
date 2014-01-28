import random
import math
import scipy
import scipy.special
import numpy.random as npr
from utils import simulateCategorical, logDensityCategorical, simulateDirichlet, logDensityDirichlet
from psp import PSP, NullRequestPSP, RandomPSP
from sp import SP,SPAux
from lkernel import LKernel, DefaultAAALKernel
from nose.tools import assert_equal,assert_greater_equal
import copy

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
class BetaBernoulliSPAux(SPAux):
  def __init__(self):
    self.yes = 0.0
    self.no = 0.0

  def copy(self): 
    aux = BetaBernoulliSPAux()
    aux.yes = self.yes
    aux.no = self.no
    return aux

class BetaBernoulliSP(SP):
  def constructSPAux(self): return BetaBernoulliSPAux()

class MakerCBetaBernoulliOutputPSP(PSP):
  def childrenCanAAA(self): return True

  def simulate(self,args):
    alpha = args.operandValues[0]
    beta  = args.operandValues[1]
    return BetaBernoulliSP(NullRequestPSP(), CBetaBernoulliOutputPSP(alpha, beta))

  def cts(self): return [self.yes,self.no]

class CBetaBernoulliOutputPSP(RandomPSP):
  def __init__(self,alpha,beta):
    self.alpha = alpha
    self.beta = beta

  def incorporate(self,value,args):
    spaux = args.spaux
    if value: # I produced true
      spaux.yes += 1
    else: # I produced false
      spaux.no += 1

  def unincorporate(self,value,args):
    spaux = args.spaux
    if value: # I produced true
      spaux.yes -= 1
    else: # I produced false
      spaux.no -= 1

  def simulate(self,args):
    [ctY,ctN] = args.spaux.cts()
    weight = (self.alpha + ctY) / (self.alpha + ctY + self.beta + ctN)
    return random.random() < weight

  def logDensity(self,value,args):
    [ctY,ctN] = args.spaux.cts()
    weight = (self.alpha + ctY) / (self.alpha + ctY + self.beta + ctN)
    if value == True:
      return math.log(weight)
    else:
      return math.log(1-weight)

  def logDensityOfCounts(self,aux):
    [ctY,ctN] = aux.cts()
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
    return BetaBernoulliSP(NullRequestPSP(), UBetaBernoulliOutputPSP(weight))

  def logDensity(self,value,args):
    alpha = args.operandValues[0]
    beta  = args.operandValues[1]
    assert isinstance(value,BetaBernoulliSP)
    coinWeight = value.outputPSP.weight
    return scipy.stats.beta.logpdf(coinWeight,alpha,beta)

class UBetaBernoulliAAALKernel(LKernel):
  def simulate(self,trace,oldValue,args):
    alpha = args.operandValues[0]
    beta  = args.operandValues[1]
    [ctY,ctN] = args.madeSPAux.cts()
    newWeight = scipy.stats.beta.rvs(alpha + ctY, beta + ctN)
    return BetaBernoulliSP(NullRequestPSP(), UBetaBernoulliOutputPSP(newWeight))
  # Weight is zero because it's simulating from the right distribution

class UBetaBernoulliOutputPSP(RandomPSP):
  def __init__(self,weight):
    self.weight = weight

  def incorporate(self,value,args):
    spaux = args.spaux
    if value: # I produced true
      spaux.yes += 1
    else: # I produced false
      spaux.no += 1

  def unincorporate(self,value,args):
    spaux = args.spaux
    if value: # I produced true
      spaux.yes -= 1
    else: # I produced false
      spaux.no -= 1

  def simulate(self,args): return random.random() < self.weight

  def logDensity(self,value,args):
    if value == True:
      return math.log(self.weight)
    else:
      return math.log(1-self.weight)

################### Symmetric Dirichlet
class DirMultSPAux(SPAux):
  def __init__(self,n=None,os=None):
    if os is not None: 
      self.os = os
      assert_greater_equal(min(self.os),0)
    elif n is not None: self.os = [0.0 for i in range(n)]
    else: raise Exception("Must pass 'n' or 'os' to DirMultSPAux")

  def copy(self): 
    assert_greater_equal(min(self.os),0)
    return DirMultSPAux(os = copy.copy(self.os))

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

  def constructSPAux(self): return DirMultSPAux(n=self.n)


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
    counts = [count + self.alpha for count in args.spaux.os]
    return simulateCategorical(counts,self.os)
      
  def logDensity(self,val,args):
    counts = [count + self.alpha for count in args.spaux.os]
    return logDensityCategorical(val,counts,self.os)

  def incorporate(self,val,args):
    assert_equal(type(args.spaux),DirMultSPAux)
    assert_greater_equal(min(args.spaux.os),0)
    index = self.os.index(val)
    args.spaux.os[index] += 1
    
  def unincorporate(self,val,args):
    assert_equal(type(args.spaux),DirMultSPAux)
    index = self.os.index(val)
    args.spaux.os[index] -= 1
    assert_greater_equal(min(args.spaux.os),0)
        
  def logDensityOfCounts(self,aux):
    N = sum(aux.os)
    A = self.alpha * self.n

    term1 = scipy.special.gammaln(A) - scipy.special.gammaln(N + A)
    galpha = scipy.special.gammaln(self.alpha)
    term2 = sum([scipy.special.gammaln(self.alpha + aux.os[index]) - galpha for index in range(self.n)])
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
    assert_equal(type(args.madeSPAux),DirMultSPAux)
    counts = [count + alpha for count in args.madeSPAux.os]
    newTheta = npr.dirichlet(counts)
    return DirMultSP(NullRequestPSP(),USymDirMultOutputPSP(newTheta,os),n)

class USymDirMultOutputPSP(RandomPSP):
  def __init__(self,theta,os):
    self.theta = theta
    self.os = os

  def simulate(self,args): return simulateCategorical(self.theta,self.os)

  def logDensity(self,val,args): return logDensityCategorical(val,self.theta,self.os)

  def incorporate(self,val,args):
    assert_equal(type(args.spaux),DirMultSPAux)
    assert_greater_equal(min(args.spaux.os),0)
    index = self.os.index(val)
    args.spaux.os[index] += 1
    
  def unincorporate(self,val,args):
    assert_equal(type(args.spaux),DirMultSPAux)
    index = self.os.index(val)
    args.spaux.os[index] -= 1
    assert_greater_equal(min(args.spaux.os),0)

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
    counts = [count + alpha for (count,alpha) in zip(args.spaux.os,self.alpha)]
    return simulateCategorical(counts,self.os)
      
  def logDensity(self,val,args):
    counts = [count + alpha for (count,alpha) in zip(args.spaux.os,self.alpha)]
    return logDensityCategorical(val,counts,self.os)

  def incorporate(self,val,args):
    assert_equal(type(args.spaux),DirMultSPAux)
    assert_greater_equal(min(args.spaux.os),0)
    index = self.os.index(val)
    args.spaux.os[index] += 1
    
  def unincorporate(self,val,args):
    assert_equal(type(args.spaux),DirMultSPAux)
    index = self.os.index(val)
    args.spaux.os[index] -= 1
    assert_greater_equal(min(args.spaux.os),0)
        
  def logDensityOfCounts(self,aux):
    assert_equal(type(aux),DirMultSPAux)
    N = sum(aux.os)
    A = sum(self.alpha)

    term1 = scipy.special.gammaln(A) - scipy.special.gammaln(N + A)
    term2 = sum([scipy.special.gammaln(alpha + count) - scipy.special.gammaln(alpha) for (alpha,count) in zip(self.alpha,aux.os)])
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
    assert_equal(type(args.madeSPAux),DirMultSPAux)
    counts = [count + a for (count,a) in zip(args.madeSPAux.os,alpha)]
    newTheta = npr.dirichlet(counts)
    return DirMultSP(NullRequestPSP(),UDirMultOutputPSP(newTheta,os),len(alpha))

class UDirMultOutputPSP(RandomPSP):
  def __init__(self,theta,os):
    self.theta = theta
    self.os = os

  def simulate(self,args): return simulateCategorical(self.theta,self.os)

  def logDensity(self,val,args): return logDensityCategorical(val,self.theta,self.os)

  def incorporate(self,val,args):
    assert_equal(type(args.spaux),DirMultSPAux)
    assert_greater_equal(min(args.spaux.os),0)
    index = self.os.index(val)
    args.spaux.os[index] += 1
    
  def unincorporate(self,val,args):
    assert_equal(type(args.spaux),DirMultSPAux)
    index = self.os.index(val)
    args.spaux.os[index] -= 1
    assert_greater_equal(min(args.spaux.os),0)
