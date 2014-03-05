import copy
from nose.tools import assert_greater_equal # assert_greater_equal is metaprogrammed pylint:disable=no-name-in-module
import scipy.special
import numpy.random as npr

from lkernel import LKernel
from sp import VentureSP,SPAux
from psp import PSP, NullRequestPSP, RandomPSP, TypedPSP
from utils import simulateCategorical, logDensityCategorical, simulateDirichlet, logDensityDirichlet
from value import AnyType, VentureAtom

#### Directly sampling simplexes

class DirichletOutputPSP(RandomPSP):

  def simulate(self,args):
    alpha = args.operandValues[0]
    return simulateDirichlet(alpha)
    
  def logDensity(self,val,args):
    alpha = args.operandValues[0]
    return logDensityDirichlet(val,alpha)

  def description(self,name):
    return "(%s <list alpha>) -> <simplex>" % name

class SymmetricDirichletOutputPSP(RandomPSP):

  def simulate(self,args):
    (alpha,n) = (float(args.operandValues[0]),int(args.operandValues[1]))
    return simulateDirichlet([alpha for _ in range(n)])
    
  def logDensity(self,val,args):
    (alpha,n) = (float(args.operandValues[0]),int(args.operandValues[1]))
    return logDensityDirichlet(val,[alpha for _ in range(n)])

  def description(self,name):
    return "(%s alpha n) -> <simplex>" % name

#### Common aux for AAA dirichlet distributions

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

class DirMultSP(VentureSP):
  def __init__(self,requestPSP,outputPSP,n):
    super(DirMultSP,self).__init__(requestPSP,outputPSP)
    self.n = n

  def constructSPAux(self): return DirMultSPAux(n=self.n)

#### Collapsed dirichlet multinomial

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

#### Uncollapsed dirichlet multinomial

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

  def weightBound(self, _trace, _newValue, _oldValue, _args): return 0

class UDirMultOutputPSP(RandomPSP):
  def __init__(self,theta,os):
    self.theta = theta
    self.os = os

  def simulate(self,args): return simulateCategorical(self.theta,self.os)

  def logDensity(self, val, _args): return logDensityCategorical(val, self.theta, self.os)

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

#### Collapsed symmetric dirichlet multinomial

class MakerCSymDirMultOutputPSP(PSP):
  def simulate(self,args):
    (alpha,n) = (float(args.operandValues[0]),int(args.operandValues[1]))
    os = args.operandValues[2] if len(args.operandValues) > 2 else [VentureAtom(i) for i in range(n)]
    output = TypedPSP([], AnyType(), CSymDirMultOutputPSP(alpha,n,os))
    return DirMultSP(NullRequestPSP(),output,n)

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

#### Uncollapsed symmetric dirichlet multinomial

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

  def weightBound(self, _trace, _newValue, _oldValue, _args): return 0

class USymDirMultOutputPSP(RandomPSP):
  def __init__(self,theta,os):
    self.theta = theta
    self.os = os

  def simulate(self,args): return simulateCategorical(self.theta,self.os)

  def logDensity(self, val, _args): return logDensityCategorical(val, self.theta, self.os)

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
