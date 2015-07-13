# Copyright (c) 2013, 2014 MIT Probabilistic Computing Project.
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

import copy
import scipy.special
import numpy.random as npr
import math

from lkernel import SimulationAAALKernel
from sp import SP, VentureSPRecord, SPAux, SPType
from psp import DeterministicPSP, DeterministicMakerAAAPSP, NullRequestPSP, RandomPSP, TypedPSP
from utils import simulateDirichlet, logDensityDirichlet
from value import VentureAtom
from types import AnyType
from exception import VentureValueError
from range_tree import Node, sample

#### Directly sampling simplexes

class DirichletOutputPSP(RandomPSP):

  def simulate(self,args):
    alpha = args.operandValues()[0]
    return simulateDirichlet(alpha)
    
  def logDensity(self,val,args):
    alpha = args.operandValues()[0]
    return logDensityDirichlet(val,alpha)

  def description(self,name):
    return "  (%s alphas) samples a simplex point according to the given Dirichlet distribution." % name

class SymmetricDirichletOutputPSP(RandomPSP):

  def simulate(self,args):
    (alpha,n) = args.operandValues()
    return simulateDirichlet([float(alpha) for _ in range(int(n))])
    
  def logDensity(self,val,args):
    (alpha,n) = args.operandValues()
    return logDensityDirichlet(val,[float(alpha) for _ in range(int(n))])

  def description(self,name):
    return "  (%s alpha n) samples a simplex point according to the symmetric Dirichlet distribution on n dimensions with concentration parameter alpha." % name

#### Common classes for AAA dirichlet distributions

class DirMultSPAux(SPAux):
  def __init__(self,n=None,counts=None):
    if counts is not None: 
      self.counts = counts
    elif n is not None:
      self.counts = Node([0]*n)
    else: raise Exception("Must pass 'n' or 'counts' to DirMultSPAux")

  def copy(self):
    return DirMultSPAux(counts = copy.deepcopy(self.counts))

class DirMultSP(SP):
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
      'counts': spaux.counts.leaves()
    }
    

#### Collapsed dirichlet multinomial

class MakerCDirMultOutputPSP(DeterministicMakerAAAPSP):
  def simulate(self,args):
    vals = args.operandValues()
    alpha = vals[0]
    os = vals[1] if len(vals) > 1 else [VentureAtom(i) for i in range(len(alpha))]
    if not len(os) == len(alpha):
      raise VentureValueError("Set of objects to choose from is the wrong length")
    output = TypedPSP(CDirMultOutputPSP(alpha,os), SPType([], AnyType()))
    return VentureSPRecord(DirMultSP(NullRequestPSP(),output,alpha,len(alpha)))

  def description(self,name):
    return "  (%s alphas objects) returns a sampler for a collapsed Dirichlet multinomial model.  If the objects argument is given, the sampler will return one of those objects on each call; if not, it will return one of n <atom>s where n is the length of the list of alphas.  It is an error if the list of objects is supplied and has different length from the list of alphas.  While this procedure itself is deterministic, the returned sampler is stochastic." % name

class CDirMultOutputPSP(RandomPSP):
  def __init__(self,alpha,os):
    self.alpha = Node(alpha)
    self.os = os
    self.index = dict((val, i) for (i, val) in enumerate(os))

  def simulate(self,args):
    index = sample(self.alpha, args.spaux().counts)
    return self.os[index]
      
  def logDensity(self,val,args):
    index = self.index[val]
    aux = args.spaux()
    num = aux.counts[index] + self.alpha[index]
    denom = aux.counts.total + self.alpha.total
    return math.log(num/denom)

  def incorporate(self,val,args):
    aux = args.spaux()
    assert isinstance(aux,DirMultSPAux)
    index = self.index[val]
    assert aux.counts[index] >= 0
    aux.counts.increment(index)
    
  def unincorporate(self,val,args):
    aux = args.spaux()
    assert isinstance(aux,DirMultSPAux)
    index = self.index[val]
    aux.counts.decrement(index)
    assert aux.counts[index] >= 0
        
  def enumerateValues(self, _args):
    return self.os

  def logDensityOfCounts(self,aux):
    assert isinstance(aux,DirMultSPAux)
    N = aux.counts.total
    A = self.alpha.total

    term1 = scipy.special.gammaln(A) - scipy.special.gammaln(N + A)
    term2 = sum([scipy.special.gammaln(alpha + count) - scipy.special.gammaln(alpha) for (alpha,count) in zip(self.alpha,aux.counts)])
    return term1 + term2

#### Uncollapsed dirichlet multinomial

class MakerUDirMultOutputPSP(RandomPSP):
  def childrenCanAAA(self): return True
  def getAAALKernel(self): return UDirMultAAALKernel()

  def simulate(self,args):
    vals = args.operandValues()
    alpha = vals[0]
    n = len(alpha)
    os = vals[1] if len(vals) > 1 else [VentureAtom(i) for i in range(n)]
    if not len(os) == n:
      raise VentureValueError("Set of objects to choose from is the wrong length")
    theta = npr.dirichlet(alpha)
    output = TypedPSP(UDirMultOutputPSP(theta,os), SPType([], AnyType()))
    return VentureSPRecord(DirMultSP(NullRequestPSP(),output,alpha,n))

  def logDensity(self,value,args):
    alpha = args.operandValues()[0]
    assert isinstance(value, VentureSPRecord)
    assert isinstance(value.sp, DirMultSP)
    assert isinstance(value.sp.outputPSP, TypedPSP)
    assert isinstance(value.sp.outputPSP.psp, UDirMultOutputPSP)
    return logDensityDirichlet(value.sp.outputPSP.psp.theta,alpha)

  def description(self,name):
    return "  %s is an uncollapsed variant of make_dir_mult." % name

class UDirMultAAALKernel(SimulationAAALKernel):
  def simulate(self, _trace, args):
    vals = args.operandValues()
    alpha = vals[0]
    os = vals[1] if len(vals) > 1 else [VentureAtom(i) for i in range(len(alpha))]
    assert isinstance(args.madeSPAux,DirMultSPAux)
    counts = [count + a for (count,a) in zip(args.madeSPAux.counts,alpha)]
    newTheta = npr.dirichlet(counts)
    output = TypedPSP(UDirMultOutputPSP(newTheta,os), SPType([], AnyType()))
    return VentureSPRecord(DirMultSP(NullRequestPSP(),output,alpha,len(alpha)), args.madeSPAux)

  def weight(self, _trace, _newValue, _args):
    # Gibbs step, samples exactly from the local posterior.  Being a
    # AAALKernel, this one gets to cancel against the likelihood as
    # well as the prior.
    return 0

  def weightBound(self, _trace, _value, _args): return 0

class UDirMultOutputPSP(RandomPSP):
  def __init__(self,theta,os):
    self.theta = Node(theta)
    self.os = os
    self.index = dict((val, i) for (i, val) in enumerate(os))

  def simulate(self, _args):
    index = sample(self.theta)
    return self.os[index]

  def logDensity(self, val, _args):
    index = self.index[val]
    return math.log(self.theta[index])

  def incorporate(self,val,args):
    aux = args.spaux()
    assert isinstance(aux,DirMultSPAux)
    index = self.index[val]
    assert aux.counts[index] >= 0
    aux.counts.increment(index)
    
  def unincorporate(self,val,args):
    aux = args.spaux()
    assert isinstance(aux,DirMultSPAux)
    index = self.index[val]
    aux.counts.decrement(index)
    assert aux.counts[index] >= 0

  def enumerateValues(self, _args):
    return self.os

#### Collapsed symmetric dirichlet multinomial

class MakerCSymDirMultOutputPSP(DeterministicMakerAAAPSP):
  def simulate(self,args):
    vals = args.operandValues()
    (alpha,n) = (float(vals[0]),int(vals[1]))
    os = vals[2] if len(vals) > 2 else [VentureAtom(i) for i in range(n)]
    if not len(os) == n:
      raise VentureValueError("Set of objects to choose from is the wrong length")
    output = TypedPSP(CSymDirMultOutputPSP(alpha,n,os), SPType([], AnyType()))
    return VentureSPRecord(DirMultSP(NullRequestPSP(),output,alpha,n))

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
    N = aux.counts.total
    A = len(aux.counts) * 1.0
    gamma_one = scipy.special.gammaln(1.0)
    term1 = scipy.special.gammaln(A) - scipy.special.gammaln(N+A)
    return term1 + sum([scipy.special.gammaln(1+count) - gamma_one for count in aux.counts])

  def description(self,name):
    return "  %s is a symmetric variant of make_dir_mult." % name

class CSymDirMultOutputPSP(CDirMultOutputPSP):
  def __init__(self,alpha,n,os):
    super(CSymDirMultOutputPSP, self).__init__([alpha] * n, os)

#### Uncollapsed symmetric dirichlet multinomial

class MakerUSymDirMultOutputPSP(RandomPSP):
  def childrenCanAAA(self): return True
  def getAAALKernel(self): return USymDirMultAAALKernel()

  def simulate(self,args):
    vals = args.operandValues()
    (alpha,n) = (float(vals[0]),int(vals[1]))
    os = vals[2] if len(vals) > 2 else [VentureAtom(i) for i in range(n)]
    if not len(os) == n:
      raise VentureValueError("Set of objects to choose from is the wrong length")
    theta = npr.dirichlet([alpha for _ in range(n)])
    output = TypedPSP(USymDirMultOutputPSP(theta,os), SPType([], AnyType()))
    return VentureSPRecord(DirMultSP(NullRequestPSP(),output,alpha,n))

  def logDensity(self,value,args):
    (alpha,n) = args.operandValues()
    assert isinstance(value, VentureSPRecord)
    assert isinstance(value.sp, DirMultSP)
    assert isinstance(value.sp.outputPSP, TypedPSP)
    assert isinstance(value.sp.outputPSP.psp, USymDirMultOutputPSP)
    return logDensityDirichlet(value.sp.outputPSP.psp.theta, [float(alpha) for _ in range(int(n))])

  def description(self,name):
    return "  %s is an uncollapsed symmetric variant of make_dir_mult." % name

class USymDirMultAAALKernel(SimulationAAALKernel):
  def simulate(self, _trace, args):
    vals = args.operandValues()
    (alpha,n) = (float(vals[0]),int(vals[1]))
    os = vals[2] if len(vals) > 2 else [VentureAtom(i) for i in range(n)]
    assert isinstance(args.madeSPAux,DirMultSPAux)
    counts = [count + alpha for count in args.madeSPAux.counts]
    newTheta = npr.dirichlet(counts)
    output = TypedPSP(USymDirMultOutputPSP(newTheta,os), SPType([], AnyType()))
    return VentureSPRecord(DirMultSP(NullRequestPSP(),output,alpha,n), args.madeSPAux)

  def weight(self, _trace, _newValue, _args):
    # Gibbs step, samples exactly from the local posterior.  Being a
    # AAALKernel, this one gets to cancel against the likelihood as
    # well as the prior.
    return 0

  def weightBound(self, _trace, _value, _args): return 0

class USymDirMultOutputPSP(UDirMultOutputPSP):
  pass
