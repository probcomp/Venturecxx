import copy
import scipy.special
import numpy.random as npr
import math

from lkernel import LKernel
from sp import VentureSP, SPAux, SPType
from psp import DeterministicPSP, NullRequestPSP, RandomPSP, TypedPSP
from utils import simulateCategorical, logDensityCategorical, simulateDirichlet, logDensityDirichlet
from value import AnyType, VentureAtom
from exception import VentureValueError

#### Directly sampling simplexes

class DirichletOutputPSP(RandomPSP):

  def simulate(self,args):
    alpha = args.operandValues[0]
    return simulateDirichlet(alpha)
    
  def logDensity(self,val,args):
    alpha = args.operandValues[0]
    return logDensityDirichlet(val,alpha)

  def description(self,name):
    return "  (%s alphas) samples a simplex point according to the given Dirichlet distribution." % name

class SymmetricDirichletOutputPSP(RandomPSP):

  def simulate(self,args):
    (alpha,n) = (float(args.operandValues[0]),int(args.operandValues[1]))
    return simulateDirichlet([alpha for _ in range(n)])
    
  def logDensity(self,val,args):
    (alpha,n) = (float(args.operandValues[0]),int(args.operandValues[1]))
    return logDensityDirichlet(val,[alpha for _ in range(n)])

  def description(self,name):
    return "  (%s alpha n) samples a simplex point according to the symmetric Dirichlet distribution on n dimensions with concentration parameter alpha." % name

#### Common classes for AAA dirichlet distributions

class DirMultSPAux(SPAux):
  def __init__(self,n=None,os=None):
    if os is not None: 
      self.os = os
      self.total = sum(os)
      assert min(self.os) >= 0
    elif n is not None:
      self.os = [0.0 for _ in range(n)]
      self.total = 0
    else: raise Exception("Must pass 'n' or 'os' to DirMultSPAux")

  def copy(self): 
    assert min(self.os) >= 0
    return DirMultSPAux(os = copy.copy(self.os))

class DirMultSP(VentureSP):
  def __init__(self,requestPSP,outputPSP,alpha,n):
    super(DirMultSP,self).__init__(requestPSP,outputPSP)
    self.alpha = alpha
    self.n = n

  def constructSPAux(self): return DirMultSPAux(n=self.n)
  def show(self,spaux):
    types = {
      CDirMultOutputPSP: 'dir_mult',
      UDirMultOutputPSP: 'uc_dir_mult',
      CSymDirMultOutputPSP: 'sym_dir_mult',
      USymDirMultOutputPSP: 'uc_sym_dir_mult'
    }
    return {
      'type': types[type(self.outputPSP.psp)],
      'alpha': self.alpha,
      'n': self.n,
      'counts': spaux.os
    }
    

#### Collapsed dirichlet multinomial

class MakerCDirMultOutputPSP(DeterministicPSP):
  def simulate(self,args):
    alpha = args.operandValues[0]
    os = args.operandValues[1] if len(args.operandValues) > 1 else [VentureAtom(i) for i in range(len(alpha))]
    if not len(os) == len(alpha):
      raise VentureValueError("Set of objets to choose from is the wrong length")
    output = TypedPSP(CDirMultOutputPSP(alpha,os), SPType([], AnyType()))
    return DirMultSP(NullRequestPSP(),output,alpha,len(alpha))

  def childrenCanAAA(self): return True

  def description(self,name):
    return "  (%s alphas objects) returns a sampler for a collapsed Dirichlet multinomial model.  If the objects argument is given, the sampler will return one of those objects on each call; if not, it will return one of n <atom>s where n is the length of the list of alphas.  It is an error if the list of objects is supplied and has different length from the list of alphas.  While this procedure itself is deterministic, the returned sampler is stochastic." % name

class CDirMultOutputPSP(RandomPSP):
  def __init__(self,alpha,os):
    self.alpha = alpha
    self.total = sum(alpha)
    self.os = os
    self.index = dict((val, i) for (i, val) in enumerate(os))

  def simulate(self,args):
    counts = [count + alpha for (count,alpha) in zip(args.spaux.os,self.alpha)]
    return simulateCategorical(counts,self.os)
      
  def logDensity(self,val,args):
    index = self.index[val]
    num = args.spaux.os[index] + self.alpha[index]
    denom = args.spaux.total + self.total
    return math.log(num/denom)

  def incorporate(self,val,args):
    assert isinstance(args.spaux,DirMultSPAux)
    index = self.index[val]
    assert args.spaux.os[index] >= 0
    args.spaux.os[index] += 1
    args.spaux.total += 1
    
  def unincorporate(self,val,args):
    assert isinstance(args.spaux,DirMultSPAux)
    index = self.index[val]
    args.spaux.os[index] -= 1
    args.spaux.total -= 1
    assert args.spaux.os[index] >= 0
        
  def enumerateValues(self,args):
    return self.os

  def logDensityOfCounts(self,aux):
    assert isinstance(aux,DirMultSPAux)
    N = aux.total
    A = self.total

    term1 = scipy.special.gammaln(A) - scipy.special.gammaln(N + A)
    term2 = sum([scipy.special.gammaln(alpha + count) - scipy.special.gammaln(alpha) for (alpha,count) in zip(self.alpha,aux.os)])
    return term1 + term2

#### Uncollapsed dirichlet multinomial

class MakerUDirMultOutputPSP(RandomPSP):
  def childrenCanAAA(self): return True
  def getAAALKernel(self): return UDirMultAAALKernel()

  def simulate(self,args):
    alpha = args.operandValues[0]
    n = len(alpha)
    os = args.operandValues[1] if len(args.operandValues) > 1 else [VentureAtom(i) for i in range(n)]
    if not len(os) == n:
      raise VentureValueError("Set of objets to choose from is the wrong length")
    theta = npr.dirichlet(alpha)
    output = TypedPSP(UDirMultOutputPSP(theta,os), SPType([], AnyType()))
    return DirMultSP(NullRequestPSP(),output,alpha,n)

  def logDensity(self,value,args):
    alpha = args.operandValues[0]
    assert isinstance(value, DirMultSP)
    assert isinstance(value.outputPSP, TypedPSP)
    assert isinstance(value.outputPSP.psp, UDirMultOutputPSP)
    return logDensityDirichlet(value.outputPSP.psp.theta,alpha)

  def description(self,name):
    return "  %s is an uncollapsed variant of make_dir_mult." % name

class UDirMultAAALKernel(LKernel):
  def simulate(self,trace,oldValue,args):
    alpha = args.operandValues[0]
    os = args.operandValues[1] if len(args.operandValues) > 1 else [VentureAtom(i) for i in range(len(alpha))]
    assert isinstance(args.madeSPAux,DirMultSPAux)
    counts = [count + a for (count,a) in zip(args.madeSPAux.os,alpha)]
    newTheta = npr.dirichlet(counts)
    output = TypedPSP(UDirMultOutputPSP(newTheta,os), SPType([], AnyType()))
    return DirMultSP(NullRequestPSP(),output,alpha,len(alpha))

  def weightBound(self, _trace, _newValue, _oldValue, _args): return 0

class UDirMultOutputPSP(RandomPSP):
  def __init__(self,theta,os):
    self.theta = theta
    self.os = os
    self.index = dict((val, i) for (i, val) in enumerate(os))

  def simulate(self,args): return simulateCategorical(self.theta,self.os)

  def logDensity(self, val, _args):
    index = self.index[val]
    return math.log(self.theta[index])

  def incorporate(self,val,args):
    assert isinstance(args.spaux,DirMultSPAux)
    index = self.index[val]
    assert args.spaux.os[index] >= 0
    args.spaux.os[index] += 1
    
  def unincorporate(self,val,args):
    assert isinstance(args.spaux,DirMultSPAux)
    index = self.index[val]
    args.spaux.os[index] -= 1
    assert args.spaux.os[index] >= 0

  def enumerateValues(self,args):
    return self.os

#### Collapsed symmetric dirichlet multinomial

class MakerCSymDirMultOutputPSP(DeterministicPSP):
  def simulate(self,args):
    (alpha,n) = (float(args.operandValues[0]),int(args.operandValues[1]))
    os = args.operandValues[2] if len(args.operandValues) > 2 else [VentureAtom(i) for i in range(n)]
    if not len(os) == n:
      raise VentureValueError("Set of objets to choose from is the wrong length")
    output = TypedPSP(CSymDirMultOutputPSP(alpha,n,os), SPType([], AnyType()))
    return DirMultSP(NullRequestPSP(),output,alpha,n)

  def childrenCanAAA(self): return True

  def madeSpLogDensityOfCountsBound(self, aux):
    """Upper bound the log density the made SP may report for its
    counts, up to arbitrary additions to the aux (but not removals
    from it), and up to arbitrary changes to the args wherewith the
    maker is simulated."""
    # TODO Communicate the maker's fixed parameters here for a more
    # precise bound
    # TODO In the case where alpha is required to be an integer, I
    # think the log density of the counts is maximized for all
    # values being as small as possible.
    # TODO Can the aux ever be null?
    # TODO Do the math properly, esp. for alpha < 1
    N = sum(aux.os)
    A = len(aux.os) * 1.0
    gamma_one = scipy.special.gammaln(1.0)
    term1 = scipy.special.gammaln(A) - scipy.special.gammaln(N+A)
    return term1 + sum([scipy.special.gammaln(1+o) - gamma_one for o in aux.os])

  def description(self,name):
    return "  %s is a symmetric variant of make_dir_mult." % name

class CSymDirMultOutputPSP(RandomPSP):
  def __init__(self,alpha,n,os):
    self.alpha = alpha
    self.n = n
    self.os = os
    self.index = dict((val, i) for (i, val) in enumerate(os))

  def simulate(self,args):
    counts = [count + self.alpha for count in args.spaux.os]
    return simulateCategorical(counts,self.os)
      
  def logDensity(self,val,args):
    index = self.index[val]
    num = args.spaux.os[index] + self.alpha
    denom = args.spaux.total + self.alpha * self.n
    return math.log(num/denom)

  def incorporate(self,val,args):
    assert isinstance(args.spaux,DirMultSPAux)
    index = self.index[val]
    assert args.spaux.os[index] >= 0
    args.spaux.os[index] += 1
    args.spaux.total += 1
    
  def unincorporate(self,val,args):
    assert isinstance(args.spaux,DirMultSPAux)
    index = self.index[val]
    args.spaux.os[index] -= 1
    args.spaux.total -= 1
    assert args.spaux.os[index] >= 0
        
  def enumerateValues(self,args):
    return self.os

  def logDensityOfCounts(self,aux):
    N = aux.total
    A = self.alpha * self.n

    term1 = scipy.special.gammaln(A) - scipy.special.gammaln(N + A)
    galpha = scipy.special.gammaln(self.alpha)
    term2 = sum([scipy.special.gammaln(self.alpha + aux.os[index]) - galpha for index in range(self.n)])
    return term1 + term2

#### Uncollapsed symmetric dirichlet multinomial

class MakerUSymDirMultOutputPSP(RandomPSP):
  def childrenCanAAA(self): return True
  def getAAALKernel(self): return USymDirMultAAALKernel()

  def simulate(self,args):
    (alpha,n) = (float(args.operandValues[0]),int(args.operandValues[1]))
    os = args.operandValues[2] if len(args.operandValues) > 2 else [VentureAtom(i) for i in range(n)]
    if not len(os) == n:
      raise VentureValueError("Set of objets to choose from is the wrong length")
    theta = npr.dirichlet([alpha for _ in range(n)])
    output = TypedPSP(USymDirMultOutputPSP(theta,os), SPType([], AnyType()))
    return DirMultSP(NullRequestPSP(),output,alpha,n)

  def logDensity(self,value,args):
    (alpha,n) = (float(args.operandValues[0]),int(args.operandValues[1]))
    assert isinstance(value, DirMultSP)
    assert isinstance(value.outputPSP, TypedPSP)
    assert isinstance(value.outputPSP.psp, USymDirMultOutputPSP)
    return logDensityDirichlet(value.outputPSP.psp.theta, [alpha for _ in range(n)])

  def description(self,name):
    return "  %s is an uncollapsed symmetric variant of make_dir_mult." % name

class USymDirMultAAALKernel(LKernel):
  def simulate(self,trace,oldValue,args):
    (alpha,n) = (float(args.operandValues[0]),int(args.operandValues[1]))
    os = args.operandValues[2] if len(args.operandValues) > 2 else [VentureAtom(i) for i in range(n)]
    assert isinstance(args.madeSPAux,DirMultSPAux)
    counts = [count + alpha for count in args.madeSPAux.os]
    newTheta = npr.dirichlet(counts)
    output = TypedPSP(USymDirMultOutputPSP(newTheta,os), SPType([], AnyType()))
    return DirMultSP(NullRequestPSP(),output,alpha,n)

  def weightBound(self, _trace, _newValue, _oldValue, _args): return 0

class USymDirMultOutputPSP(RandomPSP):
  def __init__(self,theta,os):
    self.theta = theta
    self.os = os
    self.index = dict((val, i) for (i, val) in enumerate(os))

  def simulate(self,args): return simulateCategorical(self.theta,self.os)

  def logDensity(self, val, _args):
    index = self.index[val]
    return math.log(self.theta[index])

  def incorporate(self,val,args):
    assert isinstance(args.spaux,DirMultSPAux)
    index = self.index[val]
    assert args.spaux.os[index] >= 0
    args.spaux.os[index] += 1
    
  def unincorporate(self,val,args):
    assert isinstance(args.spaux,DirMultSPAux)
    index = self.index[val]
    args.spaux.os[index] -= 1
    assert args.spaux.os[index] >= 0

  def enumerateValues(self,args):
    return self.os
