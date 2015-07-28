# Copyright (c) 2013, 2014, 2015 MIT Probabilistic Computing Project.
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

import random
import math
import scipy
import scipy.special
from utils import extendedLog, simulateCategorical, logDensityCategorical
from psp import DeterministicMakerAAAPSP, NullRequestPSP, RandomPSP, TypedPSP
from sp import SP, SPAux, VentureSPRecord, SPType
from lkernel import SimulationAAALKernel
from value import VentureAtom
import types as t
from exception import VentureValueError

class DiscretePSP(RandomPSP):
  def logDensityBound(self, _x, _args): return 0

class BernoulliOutputPSP(DiscretePSP):
  def simulate(self,args):
    vals = args.operandValues()
    p = vals[0] if vals else 0.5
    return random.random() < p

  def logDensity(self,val,args):
    vals = args.operandValues()
    p = vals[0] if vals else 0.5
    if val: return extendedLog(p)
    else: return extendedLog(1 - p)

  def gradientOfLogDensity(self, val, args):
    vals = args.operandValues()
    p = vals[0] if vals else 0.5
    deriv = 1/p if val else -1 / (1 - p)
    return (0, [deriv])

  def enumerateValues(self,args):
    vals = args.operandValues()
    p = vals[0] if vals else 0.5
    if p == 1: return [True]
    elif p == 0: return [False]
    else: return [True,False]

  def description(self,name):
    return "  %s(p) returns true with probability p and false otherwise.  If omitted, p is taken to be 0.5." % name

class LogBernoulliOutputPSP(DiscretePSP):
  def simulate(self,args):
    logp = args.operandValues()[0]
    return math.log(random.random()) < logp

  def logDensity(self,val,args):
    logp = args.operandValues()[0]
    if val: return logp
    else: return extendedLog(1 - math.exp(logp))

  def gradientOfLogDensity(self, val, args):
    logp = args.operandValues()[0]
    deriv = 1 if val else 1 / (1 - math.exp(-logp))
    return (0, [deriv])

  def enumerateValues(self,args):
    logp = args.operandValues()[0]
    if logp == 0: return [True]
    elif logp == float('-inf'): return [False]
    else: return [True,False]

  def description(self,name):
    return "  %s(p) returns true with probability exp(p) and false otherwise.  This is useful for modeling very low probability events, because it does not suffer the underflow that %s(exp(p)) would." % (name, name)

class BinomialOutputPSP(DiscretePSP):
  def simulate(self,args):
    (n,p) = args.operandValues()
    return scipy.stats.binom.rvs(n,p)

  def logDensity(self,val,args):
    (n,p) = args.operandValues()
    return scipy.stats.binom.logpmf(val,n,p)

  def enumerateValues(self,args):
    (n,p) = args.operandValues()
    if p == 1: return [n]
    elif p == 0: return [0]
    else: return [i for i in range(int(n)+1)]

  def description(self,name):
    return "  %s(n, p) simulates flipping n Bernoulli trials independently with probability p and returns the total number of successes." % name


class CategoricalOutputPSP(DiscretePSP):
  # (categorical ps outputs)
  def simulate(self,args):
    vals = args.operandValues()
    if len(vals) == 1: # Default values to choose from
      return simulateCategorical(vals[0], [VentureAtom(i) for i in range(len(vals[0]))])
    else:
      if not len(vals[0]) == len(vals[1]):
        raise VentureValueError("Categorical passed different length arguments.")
      return simulateCategorical(*vals)

  def logDensity(self,val,args):
    vals = args.operandValues()
    if len(vals) == 1: # Default values to choose from
      return logDensityCategorical(val, vals[0], [VentureAtom(i) for i in range(len(vals[0]))])
    else:
      return logDensityCategorical(val,*vals)

  def enumerateValues(self,args):
    vals = args.operandValues()
    indexes = [i for i, p in enumerate(vals[0]) if p > 0]
    if len(vals) == 1: return indexes
    else: return [vals[1][i] for i in indexes]

  def description(self,name):
    return "  %s(weights, objects) samples a categorical with the given weights.  In the one argument case, returns the index of the chosen option as an atom; in the two argument case returns the item at that index in the second argument.  It is an error if the two arguments have different length." % name

class UniformDiscreteOutputPSP(DiscretePSP):
  def simulate(self,args):
    vals = args.operandValues()
    if vals[1] <= vals[0]:
      raise VentureValueError("uniform_discrete called on invalid range (%d,%d)" % (vals[0],vals[1]))
    return random.randrange(*vals)

  def logDensity(self,val,args):
    a,b = args.operandValues()
    if a <= val and val < b: return -math.log(b-a)
    else: return extendedLog(0.0)

  def enumerateValues(self,args): return range(*[int(x) for x in args.operandValues()])

  def description(self,name):
    return "  %s(start, end) samples a uniform discrete on the (start, start + 1, ..., end - 1)" % name

class PoissonOutputPSP(DiscretePSP):
  def simulate(self,args): return scipy.stats.poisson.rvs(args.operandValues()[0])
  def logDensity(self,val,args): return scipy.stats.poisson.logpmf(val,args.operandValues()[0])
  def description(self,name):
    return "  %s(lam) samples a poisson with rate lam" % name


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

  v_type = t.HomogeneousListType(t.NumberType())

  def asVentureValue(self):
    return BetaBernoulliSPAux.v_type.asVentureValue([self.yes, self.no])

  @staticmethod
  def fromVentureValue(val):
    aux = BetaBernoulliSPAux()
    (aux.yes, aux.no) = BetaBernoulliSPAux.v_type.asPython(val)
    return aux

  def cts(self): return [self.yes,self.no]

class BetaBernoulliSP(SP):
  def construxsumPAux(self): return BetaBernoulliSPAux()
  def show(self,spaux): return spaux.cts()

class MakerCBetaBernoulliOutputPSP(DeterministicMakerAAAPSP):
  def simulate(self,args):
    (alpha, beta) = args.operandValues()
    output = TypedPSP(CBetaBernoulliOutputPSP(alpha, beta), SPType([], t.BoolType()))
    return VentureSPRecord(BetaBernoulliSP(NullRequestPSP(), output))

  def description(self,name):
    return "  %s(alpha, beta) returns a collapsed beta bernoulli sampler with pseudocounts alpha (for true) and beta (for false).  While this procedure itself is deterministic, the returned sampler is stochastic." % name

class CBetaBernoulliOutputPSP(DiscretePSP):
  def __init__(self,alpha,beta):
    assert isinstance(alpha, float)
    assert isinstance(beta, float)
    self.alpha = alpha
    self.beta = beta

  def incorporate(self,value,args):
    spaux = args.spaux()
    if value: # I produced true
      spaux.yes += 1
    else: # I produced false
      spaux.no += 1

  def unincorporate(self,value,args):
    spaux = args.spaux()
    if value: # I produced true
      spaux.yes -= 1
    else: # I produced false
      spaux.no -= 1

  def simulate(self,args):
    [ctY,ctN] = args.spaux().cts()
    weight = (self.alpha + ctY) / (self.alpha + ctY + self.beta + ctN)
    return random.random() < weight

  def logDensity(self,value,args):
    [ctY,ctN] = args.spaux().cts()
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

class MakerUBetaBernoulliOutputPSP(DiscretePSP):
  def childrenCanAAA(self): return True
  def getAAALKernel(self): return UBetaBernoulliAAALKernel()

  def simulate(self,args):
    (alpha, beta) = args.operandValues()
    weight = scipy.stats.beta.rvs(alpha, beta)
    output = TypedPSP(UBetaBernoulliOutputPSP(weight), SPType([], t.BoolType()))
    return VentureSPRecord(BetaBernoulliSP(NullRequestPSP(), output))

  def logDensity(self,value,args):
    (alpha, beta) = args.operandValues()
    assert isinstance(value,VentureSPRecord)
    assert isinstance(value.sp,BetaBernoulliSP)
    coinWeight = value.sp.outputPSP.psp.weight
    return scipy.stats.beta.logpdf(coinWeight,alpha,beta)

  def description(self,name):
    return "  %s(alpha, beta) returns an uncollapsed beta bernoulli sampler with pseudocounts alpha (for true) and beta (for false)." % name

class UBetaBernoulliAAALKernel(SimulationAAALKernel):
  def simulate(self, _trace, args):
    (alpha, beta) = args.operandValues()
    madeaux = args.madeSPAux()
    [ctY,ctN] = madeaux.cts()
    newWeight = scipy.stats.beta.rvs(alpha + ctY, beta + ctN)
    output = TypedPSP(UBetaBernoulliOutputPSP(newWeight), SPType([], t.BoolType()))
    return VentureSPRecord(BetaBernoulliSP(NullRequestPSP(), output), madeaux)

  def weight(self, _trace, _newValue, _args):
    # Gibbs step, samples exactly from the local posterior.  Being a
    # AAALKernel, this one gets to cancel against the likelihood as
    # well as the prior.
    return 0

  def weightBound(self, _trace, _value, _args):
    return 0

class UBetaBernoulliOutputPSP(DiscretePSP):
  def __init__(self,weight):
    self.weight = weight

  def incorporate(self,value,args):
    spaux = args.spaux()
    if value: # I produced true
      spaux.yes += 1
    else: # I produced false
      spaux.no += 1

  def unincorporate(self,value,args):
    spaux = args.spaux()
    if value: # I produced true
      spaux.yes -= 1
    else: # I produced false
      spaux.no -= 1

  def simulate(self, _args): return random.random() < self.weight

  def logDensity(self, value, _args):
    if value == True:
      return math.log(self.weight)
    else:
      return math.log(1-self.weight)

  def logDensityOfCounts(self,aux):
    [ctY,ctN] = aux.cts()
    # TODO Do I even want the total for all consistent sequences, or
    # just for one?  The latter is the same, except for the
    # numCombinations term.
    # numCombinations = scipy.misc.comb(ctY + ctN,ctY) # TODO Do this directly in log space
    return ctY * math.log(self.weight) + ctN * math.log(1 - self.weight) # + math.log(numCombinations)

#### Non-conjugate AAA bernoulli

class MakerSuffBernoulliOutputPSP(DeterministicMakerAAAPSP):
  def simulate(self, args):
    weight = args.operandValues()[0]
    # The made SP is the same as in the conjugate case: flip coins
    # based on an explicit weight, and maintain sufficient statistics.
    output = TypedPSP(UBetaBernoulliOutputPSP(weight), SPType([], t.BoolType()))
    return VentureSPRecord(BetaBernoulliSP(NullRequestPSP(), output))

  def description(self,name):
    return "  %s(weight) returns a bernoulli sampler (weighted coin) with given weight.  The latter maintains application statistics sufficient to absorb changes to the weight in O(1) time (without traversing all the applications)." % name

  def gradientOfLogDensityOfCounts(self, aux, args):
    """The derivatives with respect to the args of the log density of the counts collected by the made SP."""
    weight = args.operandValues()[0]
    [ctY,ctN] = aux.cts()
    return [float(ctY) / weight - float(ctN) / (1 - weight)]

  def madeSpLogDensityOfCountsBound(self, _aux): return 0

class ExactlyOutputPSP(RandomPSP):
  def simulate(self, args):
    x = args.operandValues()[0]
    # The optional second argument is the error rate
    return x

  def logDensity(self, y, args):
    vals = args.operandValues()
    if len(vals) == 1:
      x = vals[0]
      epsilon = float("-inf")
    else:
      x, epsilon = vals
    if y.equal(x): return 0
    return epsilon

  def logDensityBound(self, _y, _args):
    return 0

  def description(self, _name):
    return """Force a variable to be treated as random even though its value is known.
    This deterministically returns the first argument when simulated, but
    is willing to pretend to be able to stochastically return any object.
    The second argument, if given, is the penalty (in log space) for a mismatch.
    If not given, taken to be -infinity."""

class SuffPoissonSP(SP):
# SP for Poisson, maintaining sufficient statistics.
  def construxsumPAux(self):
    return SuffPoissonSPAux()

  def show(self,spaux):
    return spaux.cts()

class SuffPoissonSPAux(SPAux):
# SPAux for Poisson. The sufficent statistics for N observations are
# ctN (number of observations) and xsum (sum of the observations).
  def __init__(self):
    self.xsum = 0.0
    self.ctN = 0.0

  def copy(self):
    aux = SuffPoissonSPAux()
    aux.xsum = self.xsum
    aux.ctN = self.ctN
    return aux

  v_type = t.HomogeneousListType(t.NumberType())

  def asVentureValue(self):
    return SuffPoissonSPAux.v_type.asVentureValue([self.xsum,
        self.ctN])

  @staticmethod
  def fromVentureValue(val):
    aux = SuffPoissonSPAux()
    (aux.xsum, aux.ctN) = SuffPoissonSPAux.v_type.asPython(val)
    return aux

  def cts(self): 
    return [self.xsum,self.ctN]


class SuffPoissonOutputPSP(DiscretePSP):
# Generic PSP maintaining sufficient statistics.
  
  def __init__(self, mu):
    self.mu = mu

  def incorporate(self, value, args):
    spaux = args.spaux()
    spaux.xsum += value
    spaux.ctN += 1

  def unincorporate(self, value, args):
    spaux = args.spaux()
    spaux.xsum -= value
    spaux.ctN -= 1

  def simulate(self, _args): 
    return scipy.stats.poisson.rvs(mu=self.mu)

  def logDensity(self, value, _args):
    return scipy.stats.poisson.logpmf(value, self.mu)

  def logDensityOfCounts(self, aux):
    [xsum, ctN] = aux.cts()
    return scipy.stats.poisson.logpmf(xsum, ctN*self.mu)


class CGammaPoissonOutputPSP(DiscretePSP):
# Collapsed Gamma Poisson PSP.
  def __init__(self, alpha, beta):
    assert isinstance(alpha, float)
    assert isinstance(beta, float)
    self.alpha = alpha
    self.beta = beta

  def incorporate(self, value, args):
    spaux = args.spaux()
    spaux.xsum += value
    spaux.ctN += 1

  def unincorporate(self, value, args):
    spaux = args.spaux()
    spaux.xsum -= value
    spaux.ctN -= 1

  def simulate(self, args):
    # Posterior predictive is Negative Binomial.
    # http://www.stat.wisc.edu/courses/st692-newton/notes.pdf#page=50
    [xsum, ctN] = args.spaux().cts()
    n = self.alpha + xsum
    p = (self.beta + ctN) / (self.beta + ctN + 1)
    return scipy.stats.nbinom.rvs(n,p)

  def logDensity(self, value, args):
    [xsum, ctN] = args.spaux().cts()
    n = self.alpha + xsum
    p = (self.beta + ctN) / (self.beta + ctN + 1)
    return scipy.stats.nbinom.logpmf(value, n, p)

  def logDensityOfCounts(self, aux):
    # The marginal loglikelihood of the data p(D) under the prior.
    # http://seor.gmu.edu/~klaskey/SYST664/Bayes_Unit3.pdf#page=42
    # Note that our parameterization is different than the reference, since
    # self.beta = 1 / ref.beta
    return scipy.special.gammaln(self.alpha + xsum) -
      scipy.special.gammaln(self.alpha) + self.alpha * math.log(self.beta) -
      (self.alpha + xsum) * math.log(self.beta + ctN)


class MakerCGammaPoissonOutputPSP(DeterministicMakerAAAPSP):
# Maker for Collapsed Gamma Poisson
  def simulate(self, args):
    (alpha, beta) = args.operandValues()
    output = TypedPSP(CGammaPoissonOutputPSP(alpha, beta), SPType([],
        t.CountType()))
    return VentureSPRecord(SuffPoissonSP(NullRequestPSP(), output))

  def description(self, name):
    return '  %s(alpha, beta) returns a collapsed Gamma Poisson sampler. '\
        'While this procedure itself is deterministic, the returned sampler '\
        'is stochastic.' % name


class MakerUGammaPoissonOutputPSP(DiscretePSP):
# Uncollapsed AAA GammaPoisson
  
  def childrenCanAAA(self):
    return True
  
  def getAAALKernel(self):
    return UGammaPoissonAAALKernel()

  def simulate(self, args):
    (alpha, beta) = args.operandValues()
    mu = scipy.stats.gamma.rvs(alpha, beta)
    output = TypedPSP(SuffPoissonOutputPSP(mu), SPType([], t.CountType()))
    return VentureSPRecord(SuffPoissonSP(NullRequestPSP(), output))

  def logDensity(self, value, args):
    assert isinstance(value,VentureSPRecord)
    assert isinstance(value.sp,SuffPoissonSP)
    (alpha, beta) = args.operandValues()
    mu = value.sp.outputPSP.psp.mu
    return scipy.stats.gamma.logpdf(mu,alpha,beta)

  def description(self, name):
    return '  %s(alpha, beta) returns an uncollapsed Gamma Poisson sampler.'

class UGammaPoissonAAALKernel(SimulationAAALKernel):
  
  def simulate(self, _trace, args):
    (alpha, beta) = args.operandValues()
    madeaux = args.madeSPAux()
    [xsum, ctN] = madeaux.cts()
    newMean = scipy.stats.gamma.rvs(alpha + xsum, beta + ctN)
    output = TypedPSP(SuffPoissonOutputPSP(newMean), SPType([], t.CountType()))
    return VentureSPRecord(SuffPoissonSP(NullRequestPSP(), output), madeaux)

  def weight(self, _trace, _newValue, _args):
    # Gibbs step, samples exactly from the local posterior.  Being a
    # AAALKernel, this one gets to cancel against the likelihood as
    # well as the prior.
    return 0

  def weightBound(self, _trace, _value, _args): return 0

class MakerSuffPoissonOutputPSP(DeterministicMakerAAAPSP):
# Non-conjugate AAA Poisson
  
  def simulate(self, args):
    mu = args.operandValues()[0]
    # The made SP is the same as in the conjugate case: flip coins
    # based on an explicit weight, and maintain sufficient statistics.
    output = TypedPSP(SuffPoissonOutputPSP(mu), SPType([], t.CountType()))
    return VentureSPRecord(SuffPoissonSP(NullRequestPSP(), output))

  def description(self,name):
    return '  %s(mu) returns Poisson sampler with given mu. '\
      'While this procedure itself is deterministic, the returned sampler '\
      'is stochastic. The latter maintains application statistics sufficient '\
      'to absorb changes to the weight in O(1) time (without traversing all '\
      'the applications.' % name

  def gradientOfLogDensityOfCounts(self, aux, args):
    """The derivatives with respect to the args of the log density of the counts
    collected by the made SP."""
    mu = args.operandValues()[0]
    [xsum, ctN] = aux.cts()
    return [-ctN + xsum / mu]

  def madeSpLogDensityOfCountsBound(self, _aux):
    return 0
