import random
import math
import scipy
import scipy.special
import numpy.random as npr
from utils import simulateCategorical, logDensityCategorical, simulateDirichlet, logDensityDirichlet
from psp import PSP, NullRequestPSP, RandomPSP
from sp import VentureSP,SPAux
from lkernel import LKernel
from nose.tools import assert_greater_equal # assert_greater_equal is metaprogrammed pylint:disable=no-name-in-module
import copy
from value import AnyType, VentureAtom, BoolType # BoolType is metaprogrammed pylint:disable=no-name-in-module
from psp import TypedPSP

class BernoulliOutputPSP(RandomPSP):
  def simulate(self,args):
    p = args.operandValues[0] if args.operandValues else 0.5
    return random.random() < p
    
  def logDensity(self,val,args):
    p = args.operandValues[0] if args.operandValues else 0.5
    if val: return math.log(p)
    else: return math.log(1 - p)

  def logDensityBound(self, _x, _args): return 0

  def enumerateValues(self,args):
    p = args.operandValues[0] if args.operandValues else 0.5
    if p == 1: return [True]
    elif p == 0: return [False]
    else: return [True,False]

  def description(self,name):
    return "(%s <number>) -> <bool>\n(%s) -> <bool>" % (name,name)

class BinomialOutputPSP(RandomPSP):
  def simulate(self,args):
    (n,p) = args.operandValues
    return scipy.stats.binom.rvs(n,p)
    
  def logDensity(self,val,args):
    (n,p) = args.operandValues
    return scipy.stats.binom.logpmf(val,n,p)

  def enumerateValues(self,args):
    (n,p) = args.operandValues
    if p == 1: return [n]
    elif p == 0: return [0]
    else: return [i for i in range(int(n)+1)]

  # TODO AXCH can we have a convention where we include the types and the meanings?
  # e.g. (%s count::Number probability::Number)
  def description(self,name):
    return "(%s <count> <probability>) -> <number>" % name


class CategoricalOutputPSP(RandomPSP):
  # (categorical ps outputs)
  def simulate(self,args):
    if len(args.operandValues) == 1: # Default values to choose from
      return simulateCategorical(args.operandValues[0], [VentureAtom(i) for i in range(len(args.operandValues[0]))])
    else:
      return simulateCategorical(*args.operandValues)

  def logDensity(self,val,args):
    if len(args.operandValues) == 1: # Default values to choose from
      return logDensityCategorical(val, args.operandValues[0], [VentureAtom(i) for i in range(len(args.operandValues[0]))])
    else:
      return logDensityCategorical(val,*args.operandValues)

  def description(self,name):
    return "(%s <simplex>) -> <number>\n(%s <simplex> <list a>) -> a\n  Samples a categorical.  In the one argument case, returns the index of the chosen option; in the two argument case returns the item at that index in the second argument.  It is an error if the two arguments have different length." % (name, name)

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

  def cts(self): return [self.yes,self.no]

class BetaBernoulliSP(VentureSP):
  def constructSPAux(self): return BetaBernoulliSPAux()

class MakerCBetaBernoulliOutputPSP(PSP):
  def childrenCanAAA(self): return True

  def simulate(self,args):
    alpha = args.operandValues[0]
    beta  = args.operandValues[1]
    output = TypedPSP([], BoolType(), CBetaBernoulliOutputPSP(alpha, beta))
    return BetaBernoulliSP(NullRequestPSP(), output)

  def description(self,name):
    return "(%s alpha beta) -> <SP () <bool>>\n  Collapsed beta Bernoulli." % name


class CBetaBernoulliOutputPSP(RandomPSP):
  def __init__(self,alpha,beta):
    assert isinstance(alpha, float)
    assert isinstance(beta, float)
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
    output = TypedPSP([], BoolType(), UBetaBernoulliOutputPSP(weight))
    return BetaBernoulliSP(NullRequestPSP(), output)

  def logDensity(self,value,args):
    alpha = args.operandValues[0]
    beta  = args.operandValues[1]
    assert isinstance(value,BetaBernoulliSP)
    coinWeight = value.outputPSP.psp.weight
    return scipy.stats.beta.logpdf(coinWeight,alpha,beta)

  def description(self,name):
    return "(%s alpha beta) -> <SP () <bool>>\n  Uncollapsed beta Bernoulli." % name

class UBetaBernoulliAAALKernel(LKernel):
  def simulate(self,trace,oldValue,args):
    alpha = args.operandValues[0]
    beta  = args.operandValues[1]
    [ctY,ctN] = args.madeSPAux.cts()
    newWeight = scipy.stats.beta.rvs(alpha + ctY, beta + ctN)
    output = TypedPSP([], BoolType(), UBetaBernoulliOutputPSP(newWeight))
    return BetaBernoulliSP(NullRequestPSP(), output)
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
    elif n is not None: self.os = [0.0 for _ in range(n)]
    else: raise Exception("Must pass 'n' or 'os' to DirMultSPAux")

  def copy(self): 
    assert_greater_equal(min(self.os),0)
    return DirMultSPAux(os = copy.copy(self.os))

class SymmetricDirichletOutputPSP(RandomPSP):

  def simulate(self,args):
    (alpha,n) = (float(args.operandValues[0]),int(args.operandValues[1]))
    return simulateDirichlet([alpha for _ in range(n)])
    
  def logDensity(self,val,args):
    (alpha,n) = (float(args.operandValues[0]),int(args.operandValues[1]))
    return logDensityDirichlet(val,[alpha for _ in range(n)])

  def description(self,name):
    return "(%s alpha n) -> <simplex>" % name

class DirMultSP(VentureSP):
  def __init__(self,requestPSP,outputPSP,n):
    super(DirMultSP,self).__init__(requestPSP,outputPSP)
    self.n = n

  def constructSPAux(self): return DirMultSPAux(n=self.n)


### Collapsed SymDirMult

class MakerCSymDirMultOutputPSP(PSP):
  def simulate(self,args):
    (alpha,n) = (float(args.operandValues[0]),int(args.operandValues[1]))
    os = args.operandValues[2] if len(args.operandValues) > 2 else [VentureAtom(i) for i in range(n)]
    output = TypedPSP([], AnyType(), CSymDirMultOutputPSP(alpha,n,os))
    return DirMultSP(NullRequestPSP(),output,n)

  def childrenCanAAA(self): return True

  def description(self,name):
    return "(%s alpha n) -> <SP () <atom>>\n(%s alpha n <array a>) -> <SP () a>\n  Collapsed symmetric Dirichlet nultinomial in n dimensions.  The two argument version returns a sampler for the dimension; the three argument version returns a sampler from the given list of options.  It is an error if the length of the given list is not n." % (name, name)

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
    assert isinstance(args.spaux,DirMultSPAux)
    assert_greater_equal(min(args.spaux.os),0)
    index = self.os.index(val)
    args.spaux.os[index] += 1
    
  def unincorporate(self,val,args):
    assert isinstance(args.spaux,DirMultSPAux)
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
    os = args.operandValues[2] if len(args.operandValues) > 2 else [VentureAtom(i) for i in range(n)]
    theta = npr.dirichlet([alpha for _ in range(n)])
    output = TypedPSP([], AnyType(), USymDirMultOutputPSP(theta,os))
    return DirMultSP(NullRequestPSP(),output,n)

  def logDensity(self,value,args):
    (alpha,n) = (float(args.operandValues[0]),int(args.operandValues[1]))
    assert isinstance(value, DirMultSP)
    assert isinstance(value.outputPSP, TypedPSP)
    assert isinstance(value.outputPSP.psp, USymDirMultOutputPSP)
    return logDensityDirichlet(value.outputPSP.psp.theta, [alpha for _ in range(n)])

  def description(self,name):
    return "(%s alpha n) -> <SP () <number>>\n(%s alpha n <list a>) -> <SP () a>\n  Uncollapsed symmetric Dirichlet nultinomial in n dimensions.  The two argument version returns a sampler for the dimension; the three argument version returns a sampler from the given list of options.  It is an error if the length of the given list is not n." % (name, name)

class USymDirMultAAALKernel(LKernel):
  def simulate(self,trace,oldValue,args):
    (alpha,n) = (float(args.operandValues[0]),int(args.operandValues[1]))
    os = args.operandValues[2] if len(args.operandValues) > 2 else [VentureAtom(i) for i in range(n)]
    assert isinstance(args.madeSPAux,DirMultSPAux)
    counts = [count + alpha for count in args.madeSPAux.os]
    newTheta = npr.dirichlet(counts)
    output = TypedPSP([], AnyType(), USymDirMultOutputPSP(newTheta,os))
    return DirMultSP(NullRequestPSP(),output,n)

class USymDirMultOutputPSP(RandomPSP):
  def __init__(self,theta,os):
    self.theta = theta
    self.os = os

  def simulate(self,args): return simulateCategorical(self.theta,self.os)

  def logDensity(self,val,args): return logDensityCategorical(val,self.theta,self.os)

  def incorporate(self,val,args):
    assert isinstance(args.spaux,DirMultSPAux)
    assert_greater_equal(min(args.spaux.os),0)
    index = self.os.index(val)
    args.spaux.os[index] += 1
    
  def unincorporate(self,val,args):
    assert isinstance(args.spaux,DirMultSPAux)
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

  def description(self,name):
    return "(%s <list alpha>) -> <simplex>" % name

### Collapsed Dirichlet-Multinomial

class MakerCDirMultOutputPSP(PSP):
  def simulate(self,args):
    alpha = args.operandValues[0]
    os = args.operandValues[1] if len(args.operandValues) > 1 else [VentureAtom(i) for i in range(len(alpha))]
    output = TypedPSP([], AnyType(), CDirMultOutputPSP(alpha,os))
    return DirMultSP(NullRequestPSP(),output,len(alpha))

  def childrenCanAAA(self): return True

  def description(self,name):
    return "(%s <list alpha>) -> <SP () <number>>\n(%s <list alpha> <list a>) -> <SP () a>\n  Collapsed Dirichlet multinomial." % (name, name)

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
    assert isinstance(args.spaux,DirMultSPAux)
    assert_greater_equal(min(args.spaux.os),0)
    index = self.os.index(val)
    args.spaux.os[index] += 1
    
  def unincorporate(self,val,args):
    assert isinstance(args.spaux,DirMultSPAux)
    index = self.os.index(val)
    args.spaux.os[index] -= 1
    assert_greater_equal(min(args.spaux.os),0)
        
  def logDensityOfCounts(self,aux):
    assert isinstance(aux,DirMultSPAux)
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
    os = args.operandValues[1] if len(args.operandValues) > 1 else [VentureAtom(i) for i in range(n)]
    theta = npr.dirichlet(alpha)
    output = TypedPSP([], AnyType(), UDirMultOutputPSP(theta,os))
    return DirMultSP(NullRequestPSP(),output,n)

  def logDensity(self,value,args):
    alpha = args.operandValues[0]
    assert isinstance(value, DirMultSP)
    assert isinstance(value.outputPSP, TypedPSP)
    assert isinstance(value.outputPSP.psp, UDirMultOutputPSP)
    return logDensityDirichlet(value.outputPSP.psp.theta,alpha)

  def description(self,name):
    return "(%s <list alpha>) -> <SP () <number>>\n(%s <list alpha> <list a>) -> <SP () a>\n  Uncollapsed Dirichlet multinomial." % (name,name)

class UDirMultAAALKernel(LKernel):
  def simulate(self,trace,oldValue,args):
    alpha = args.operandValues[0]
    os = args.operandValues[1] if len(args.operandValues) > 1 else [VentureAtom(i) for i in range(len(alpha))]
    assert isinstance(args.madeSPAux,DirMultSPAux)
    counts = [count + a for (count,a) in zip(args.madeSPAux.os,alpha)]
    newTheta = npr.dirichlet(counts)
    output = TypedPSP([], AnyType(), UDirMultOutputPSP(newTheta,os))
    return DirMultSP(NullRequestPSP(),output,len(alpha))

class UDirMultOutputPSP(RandomPSP):
  def __init__(self,theta,os):
    self.theta = theta
    self.os = os

  def simulate(self,args): return simulateCategorical(self.theta,self.os)

  def logDensity(self,val,args): return logDensityCategorical(val,self.theta,self.os)

  def incorporate(self,val,args):
    assert isinstance(args.spaux,DirMultSPAux)
    assert_greater_equal(min(args.spaux.os),0)
    index = self.os.index(val)
    args.spaux.os[index] += 1
    
  def unincorporate(self,val,args):
    assert isinstance(args.spaux,DirMultSPAux)
    index = self.os.index(val)
    args.spaux.os[index] -= 1
    assert_greater_equal(min(args.spaux.os),0)
