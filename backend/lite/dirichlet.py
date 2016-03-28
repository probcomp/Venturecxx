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

import copy
import math

import scipy.special

from venture.lite.exception import VentureValueError
from venture.lite.lkernel import PosteriorAAALKernel
from venture.lite.psp import DeterministicMakerAAAPSP
from venture.lite.psp import NullRequestPSP
from venture.lite.psp import RandomPSP
from venture.lite.psp import TypedPSP
from venture.lite.range_tree import Node, sample
from venture.lite.sp import SP, VentureSPRecord, SPAux, SPType
from venture.lite.sp_help import typed_nr
from venture.lite.sp_registry import registerBuiltinSP
from venture.lite.utils import simulateDirichlet, logDensityDirichlet
from venture.lite.utils import logDensityCategoricalSequence
from venture.lite.value import VentureInteger
import venture.lite.types as t

#### Directly sampling simplexes

class DirichletOutputPSP(RandomPSP):

  def simulate(self, args):
    alpha = args.operandValues()[0]
    return simulateDirichlet(alpha, args.args.np_rng)

  def logDensity(self, val, args):
    alpha = args.operandValues()[0]
    return logDensityDirichlet(val, alpha)

  def description(self, name):
    return "  %s(alphas) samples a simplex point according to the given " \
      "Dirichlet distribution." % name

registerBuiltinSP("dirichlet", \
  typed_nr(DirichletOutputPSP(),
           [t.HomogeneousArrayType(t.PositiveType())], t.SimplexType()))

class SymmetricDirichletOutputPSP(RandomPSP):

  def simulate(self, args):
    (alpha, n) = args.operandValues()
    return simulateDirichlet([float(alpha) for _ in range(int(n))],
                             args.args.np_rng)

  def logDensity(self, val, args):
    (alpha, n) = args.operandValues()
    return logDensityDirichlet(val, [float(alpha) for _ in range(int(n))])

  def description(self, name):
    return "  %s(alpha, n) samples a simplex point according to the " \
      "symmetric Dirichlet distribution on n dimensions with " \
      "concentration parameter alpha." % name

registerBuiltinSP("symmetric_dirichlet", \
  typed_nr(SymmetricDirichletOutputPSP(),
           [t.PositiveType(), t.CountType()], t.SimplexType()))

#### Common classes for AAA dirichlet distributions

class DirCatSPAux(SPAux):
  def __init__(self, n=None, counts=None):
    if counts is not None:
      self.counts = counts
    elif n is not None:
      self.counts = Node([0]*n)
    else: raise Exception("Must pass 'n' or 'counts' to DirCatSPAux")

  def copy(self):
    return DirCatSPAux(counts = copy.deepcopy(self.counts))

class DirCatSP(SP):
  def __init__(self, requestPSP, outputPSP, alpha, n):
    super(DirCatSP, self).__init__(requestPSP, outputPSP)
    self.alpha = alpha
    self.n = n

  def constructSPAux(self): return DirCatSPAux(n=self.n)
  def show(self, spaux):
    types = {
      CDirCatOutputPSP: 'dir_cat',
      UDirCatOutputPSP: 'uc_dir_cat',
      CSymDirCatOutputPSP: 'sym_dir_cat',
      USymDirCatOutputPSP: 'uc_sym_dir_cat'
    }
    return {
      'type': types[type(self.outputPSP.psp)],
      'alpha': self.alpha,
      'n': self.n,
      'counts': spaux.counts.leaves()
    }


#### Collapsed dirichlet categorical

class MakerCDirCatOutputPSP(DeterministicMakerAAAPSP):
  def simulate(self, args):
    vals = args.operandValues()
    alpha = vals[0]
    os = vals[1] if len(vals) > 1 \
         else [VentureInteger(i) for i in range(len(alpha))]
    if len(os) != len(alpha):
      raise VentureValueError(
        "Set of objects to choose from is the wrong length")
    output = TypedPSP(CDirCatOutputPSP(alpha, os), SPType([], t.AnyType()))
    return VentureSPRecord(DirCatSP(NullRequestPSP(), output, alpha,
                                     len(alpha)))

  def description(self, name):
    return "  %s(alphas, objects) returns a sampler for a collapsed " \
      "Dirichlet categorical model.  If the objects argument is given, " \
      "the sampler will return one of those objects on each call; if not, " \
      "it will return the index into the corresponding alpha, as an integer." \
      "  It is an error if the list of objects is supplied and " \
      "has different length from the list of alphas.  While this procedure " \
      "itself is deterministic, the returned sampler is stochastic." % name

  def gradientOfLogDensityOfData(self, aux, args):
    vals = args.operandValues()
    alphas = vals[0]
    N = aux.counts.total
    A = sum(alphas)
    term1 = scipy.special.digamma(A) - scipy.special.digamma(N + A)
    term2 = [scipy.special.digamma(alpha + count)
             - scipy.special.digamma(alpha)
             for (alpha, count) in zip(alphas, aux.counts)]
    dalphas = [term1 + t2 for t2 in term2]
    if len(vals) == 1:
      return [dalphas]
    else:
      return [dalphas, 0]

  def madeSpLogDensityOfDataBound(self, _aux):
    # Observations are discrete, so the logDensityOfData is bounded by 0.
    # Improving this bound is Github issue #468.
    return 0

class CDirCatOutputPSP(RandomPSP):
  def __init__(self, alpha, os):
    self.alpha = Node(alpha)
    self.os = os
    self.index = dict((val, i) for (i, val) in enumerate(os))

  def simulate(self, args):
    index = sample(args.args.np_rng, self.alpha, args.spaux().counts)
    return self.os[index]

  def logDensity(self, val, args):
    index = self.index[val]
    aux = args.spaux()
    num = aux.counts[index] + self.alpha[index]
    denom = aux.counts.total + self.alpha.total
    return math.log(num/denom)

  def incorporate(self, val, args):
    aux = args.spaux()
    assert isinstance(aux, DirCatSPAux)
    index = self.index[val]
    assert aux.counts[index] >= 0
    aux.counts.increment(index)

  def unincorporate(self, val, args):
    aux = args.spaux()
    assert isinstance(aux, DirCatSPAux)
    index = self.index[val]
    aux.counts.decrement(index)
    assert aux.counts[index] >= 0

  def enumerateValues(self, _args):
    return self.os

  def logDensityOfData(self, aux):
    assert isinstance(aux, DirCatSPAux)
    N = aux.counts.total
    A = self.alpha.total

    term1 = scipy.special.gammaln(A) - scipy.special.gammaln(N + A)
    term2 = sum([scipy.special.gammaln(alpha + count)
                 - scipy.special.gammaln(alpha)
                 for (alpha, count) in zip(self.alpha, aux.counts)])
    return term1 + term2

registerBuiltinSP("make_dir_cat", \
  typed_nr(MakerCDirCatOutputPSP(),
           [t.HomogeneousArrayType(t.PositiveType()), t.ArrayType()],
           SPType([], t.AnyType()), min_req_args=1))

#### Uncollapsed dirichlet categorical

class MakerUDirCatOutputPSP(RandomPSP):
  def childrenCanAAA(self): return True
  def getAAALKernel(self): return UDirCatAAALKernel(self)

  def simulate(self, args):
    vals = args.operandValues()
    alpha = vals[0]
    n = len(alpha)
    os = vals[1] if len(vals) > 1 else [VentureInteger(i) for i in range(n)]
    if len(os) != n:
      raise VentureValueError(
        "Set of objects to choose from is the wrong length")
    theta = args.args.np_rng.dirichlet(alpha)
    output = TypedPSP(UDirCatOutputPSP(theta, os), SPType([], t.AnyType()))
    return VentureSPRecord(DirCatSP(NullRequestPSP(), output, alpha, n))

  def logDensity(self, value, args):
    alpha = args.operandValues()[0]
    assert isinstance(value, VentureSPRecord)
    assert isinstance(value.sp, DirCatSP)
    assert isinstance(value.sp.outputPSP, TypedPSP)
    assert isinstance(value.sp.outputPSP.psp, UDirCatOutputPSP)
    return logDensityDirichlet(value.sp.outputPSP.psp.theta, alpha)

  def marginalLogDensityOfData(self, aux, args):
    vals = args.operandValues()
    alpha = vals[0]
    n = len(alpha)
    os = vals[1] if len(vals) > 1 else [VentureInteger(i) for i in range(n)]
    return CDirCatOutputPSP(alpha, os).logDensityOfData(aux)

  def gradientOfLogDensityOfData(self, aux, args):
    return MakerCDirCatOutputPSP().gradientOfLogDensityOfData(aux, args)

  def madeSpLogDensityOfDataBound(self, aux):
    return MakerCDirCatOutputPSP().madeSpLogDensityOfDataBound(aux)

  def description(self, name):
    return "  %s is an uncollapsed variant of make_dir_cat." % name

class UDirCatAAALKernel(PosteriorAAALKernel):
  def simulate(self, _trace, args):
    vals = args.operandValues()
    alpha = vals[0]
    os = vals[1] if len(vals) > 1 \
         else [VentureInteger(i) for i in range(len(alpha))]
    madeaux = args.madeSPAux()
    assert isinstance(madeaux, DirCatSPAux)
    counts = [count + a for (count, a) in zip(madeaux.counts, alpha)]
    newTheta = args.args.np_rng.dirichlet(counts)
    output = TypedPSP(UDirCatOutputPSP(newTheta, os), SPType([], t.AnyType()))
    return VentureSPRecord(DirCatSP(NullRequestPSP(), output, alpha,
                                     len(alpha)),
                           madeaux)

class UDirCatOutputPSP(RandomPSP):
  def __init__(self, theta, os):
    self.theta = Node(theta)
    self.os = os
    self.index = dict((val, i) for (i, val) in enumerate(os))

  def simulate(self, args):
    index = sample(args.args.np_rng, self.theta)
    return self.os[index]

  def logDensity(self, val, _args):
    index = self.index[val]
    return math.log(self.theta[index])

  def incorporate(self, val, args):
    aux = args.spaux()
    assert isinstance(aux, DirCatSPAux)
    index = self.index[val]
    assert aux.counts[index] >= 0
    aux.counts.increment(index)

  def unincorporate(self, val, args):
    aux = args.spaux()
    assert isinstance(aux, DirCatSPAux)
    index = self.index[val]
    aux.counts.decrement(index)
    assert aux.counts[index] >= 0

  def enumerateValues(self, _args):
    return self.os

registerBuiltinSP("make_uc_dir_cat", \
  typed_nr(MakerUDirCatOutputPSP(),
           [t.HomogeneousArrayType(t.PositiveType()), t.ArrayType()],
           SPType([], t.AnyType()), min_req_args=1))

#### Collapsed symmetric dirichlet categorical

class MakerCSymDirCatOutputPSP(DeterministicMakerAAAPSP):
  def simulate(self, args):
    vals = args.operandValues()
    (alpha, n) = (float(vals[0]), int(vals[1]))
    os = vals[2] if len(vals) > 2 else [VentureInteger(i) for i in range(n)]
    if len(os) != n:
      raise VentureValueError(
        "Set of objects to choose from is the wrong length")
    output = TypedPSP(CSymDirCatOutputPSP(alpha, n, os),
                      SPType([], t.AnyType()))
    return VentureSPRecord(DirCatSP(NullRequestPSP(), output, alpha, n))

  def gradientOfLogDensityOfData(self, aux, args):
    vals = args.operandValues()
    (alpha, n) = (float(vals[0]), int(vals[1]))
    N = aux.counts.total
    A = alpha*n
    term1 = scipy.special.digamma(A) - scipy.special.digamma(N + A)
    term2 = [scipy.special.digamma(alpha + count)
             - scipy.special.digamma(alpha)
             for count in aux.counts]
    dalpha = sum(term1 + t2 for t2 in term2)
    if len(vals) == 2:
      return [dalpha, 0]
    else:
      return [dalpha, 0, 0]

  def madeSpLogDensityOfDataBound(self, aux):
    N = aux.counts.total
    if N == 0:
      return 0
    empirical_freqs = [float(c) / N for c in aux.counts]
    # The prior can't do better than concentrating all mass on exactly
    # the best weights, which are the empirical ones.
    return logDensityCategoricalSequence(empirical_freqs, aux.counts)

  def description(self, name):
    return "  %s is a symmetric variant of make_dir_cat." % name

class CSymDirCatOutputPSP(CDirCatOutputPSP):
  def __init__(self, alpha, n, os):
    super(CSymDirCatOutputPSP, self).__init__([alpha] * n, os)

registerBuiltinSP("make_sym_dir_cat", \
  typed_nr(MakerCSymDirCatOutputPSP(),
           [t.PositiveType(), t.CountType(), t.ArrayType()],
           # Saying AnyType here requires the underlying psp to emit a
           # VentureValue.
           SPType([], t.AnyType()), min_req_args=2))

#### Uncollapsed symmetric dirichlet categorical

class MakerUSymDirCatOutputPSP(RandomPSP):
  def childrenCanAAA(self): return True
  def getAAALKernel(self): return USymDirCatAAALKernel(self)

  def simulate(self, args):
    vals = args.operandValues()
    (alpha, n) = (float(vals[0]), int(vals[1]))
    os = vals[2] if len(vals) > 2 else [VentureInteger(i) for i in range(n)]
    if len(os) != n:
      raise VentureValueError(
        "Set of objects to choose from is the wrong length")
    theta = args.args.np_rng.dirichlet([alpha for _ in range(n)])
    output = TypedPSP(USymDirCatOutputPSP(theta, os), SPType([], t.AnyType()))
    return VentureSPRecord(DirCatSP(NullRequestPSP(), output, alpha, n))

  def logDensity(self, value, args):
    vals = args.operandValues()
    (alpha, n) = (float(vals[0]), int(vals[1]))
    assert isinstance(value, VentureSPRecord)
    assert isinstance(value.sp, DirCatSP)
    assert isinstance(value.sp.outputPSP, TypedPSP)
    assert isinstance(value.sp.outputPSP.psp, USymDirCatOutputPSP)
    return logDensityDirichlet(value.sp.outputPSP.psp.theta,
                               [float(alpha) for _ in range(int(n))])

  def marginalLogDensityOfData(self, aux, args):
    vals = args.operandValues()
    (alpha, n) = (float(vals[0]), int(vals[1]))
    os = vals[2] if len(vals) > 2 else [VentureInteger(i) for i in range(n)]
    return CSymDirCatOutputPSP(alpha, n, os).logDensityOfData(aux)

  def gradientOfLogDensityOfData(self, aux, args):
    return MakerCSymDirCatOutputPSP().gradientOfLogDensityOfData(aux, args)

  def madeSpLogDensityOfDataBound(self, aux):
    return MakerCSymDirCatOutputPSP().madeSpLogDensityOfDataBound(aux)

  def description(self, name):
    return "  %s is an uncollapsed symmetric variant of make_dir_cat." % name

class USymDirCatAAALKernel(PosteriorAAALKernel):
  def simulate(self, _trace, args):
    vals = args.operandValues()
    (alpha, n) = (float(vals[0]), int(vals[1]))
    os = vals[2] if len(vals) > 2 else [VentureInteger(i) for i in range(n)]
    madeaux = args.madeSPAux()
    assert isinstance(madeaux, DirCatSPAux)
    counts = [count + alpha for count in madeaux.counts]
    newTheta = args.args.np_rng.dirichlet(counts)
    output = TypedPSP(USymDirCatOutputPSP(newTheta, os),
                      SPType([], t.AnyType()))
    return VentureSPRecord(DirCatSP(NullRequestPSP(), output, alpha, n),
                           madeaux)

class USymDirCatOutputPSP(UDirCatOutputPSP):
  pass

registerBuiltinSP("make_uc_sym_dir_cat",
                  typed_nr(MakerUSymDirCatOutputPSP(),
                           [t.PositiveType(), t.CountType(), t.ArrayType()],
                           SPType([], t.AnyType()), min_req_args=2))
