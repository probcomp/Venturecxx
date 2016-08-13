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

import math
from collections import OrderedDict

import scipy
import scipy.special

from venture.lite.exception import VentureValueError
from venture.lite.lkernel import PosteriorAAALKernel
from venture.lite.psp import DeterministicMakerAAAPSP
from venture.lite.psp import NullRequestPSP
from venture.lite.psp import RandomPSP
from venture.lite.psp import TypedPSP
from venture.lite.sp import SP
from venture.lite.sp import SPAux
from venture.lite.sp import SPType
from venture.lite.sp import VentureSPRecord
from venture.lite.sp_help import typed_nr
from venture.lite.sp_registry import registerBuiltinSP
from venture.lite.utils import d_log_logistic
from venture.lite.utils import extendedLog
from venture.lite.utils import extendedLog1p
from venture.lite.utils import logDensityCategorical
from venture.lite.utils import log_logistic
from venture.lite.utils import logit
from venture.lite.utils import simulateCategorical
from venture.lite.value import VentureInteger
import venture.lite.types as t


class DiscretePSP(RandomPSP):
  def logDensityBound(self, _x, _args):
    return 0


class BernoulliOutputPSP(DiscretePSP):
  def simulate(self, args):
    vals = args.operandValues()
    p = vals[0] if vals else 0.5
    return args.py_prng().random() < p

  def logDensity(self, val, args):
    vals = args.operandValues()
    p = vals[0] if vals else 0.5
    if val:
      return extendedLog(p)
    else:
      return extendedLog1p(-p)

  def gradientOfLogDensity(self, val, args):
    vals = args.operandValues()
    if len(vals) > 0:
      p = vals[0]
      deriv = 1/p if val else -1 / (1 - p)
      return (0, [deriv])
    else:
      return (0, [])

  def enumerateValues(self, args):
    vals = args.operandValues()
    p = vals[0] if vals else 0.5
    if p == 1:
      return [True]
    elif p == 0:
      return [False]
    else:
      return [True,False]

  def description(self, name):
    return '  %s(p) returns true with probability p and false otherwise. '\
      'If omitted, p is taken to be 0.5.' % name


registerBuiltinSP("flip", typed_nr(BernoulliOutputPSP(),
  [t.ProbabilityType()], t.BoolType(), min_req_args=0))

registerBuiltinSP("bernoulli", typed_nr(BernoulliOutputPSP(),
  [t.ProbabilityType()], t.IntegerType(), min_req_args=0))


class LogBernoulliOutputPSP(DiscretePSP):
  def simulate(self, args):
    logp = args.operandValues()[0]
    return math.log(args.py_prng().random()) < logp

  def logDensity(self, val, args):
    logp = args.operandValues()[0]
    if val: return logp
    else: return extendedLog1p(-math.exp(logp))

  def gradientOfLogDensity(self, val, args):
    logp = args.operandValues()[0]
    # If val is false, deriv = 1 / (1 - e^(-logp)), computed here with expm1.
    deriv = 1 if val else 1. / -math.expm1(-logp)
    return (0, [deriv])

  def enumerateValues(self, args):
    logp = args.operandValues()[0]
    if logp == 0: return [True]
    elif logp == float('-inf'): return [False]
    else: return [True,False]

  def description(self, name):
    return '  %s(p) returns true with probability exp(p) and false otherwise. '\
      'This is useful for modeling very low probability events, because it '\
      'does not suffer the underflow that %s(exp(p)) would.' % (name, name)


registerBuiltinSP("log_flip", typed_nr(LogBernoulliOutputPSP(),
  [t.NumberType()], t.BoolType()))

registerBuiltinSP("log_bernoulli", typed_nr(LogBernoulliOutputPSP(),
  [t.NumberType()], t.BoolType()))


class LogOddsBernoulliOutputPSP(DiscretePSP):
  def simulate(self, args):
    logodds = args.operandValues()[0]
    return logit(args.py_prng().random()) < logodds

  def logDensity(self, val, args):
    logodds = args.operandValues()[0]
    return log_logistic(logodds if val else -logodds)

  def gradientOfLogDensity(self, val, args):
    logodds = args.operandValues()[0]
    return (0, [d_log_logistic(logodds) if val else -d_log_logistic(-logodds)])

  def enumerateValues(self, args):
    logodds = args.operandValues()[0]
    inf = float('inf')
    if logodds == +inf:
      return [True]
    elif logodds == -inf:
      return [False]
    else:
      return [True, False]

  def description(self, name):
    return '  %s(logodds) returns true with specified log-odds.' \
      '  Like log_bernoulli/log_flip, this avoids rounding low probabilities' \
      ' to zero.'


registerBuiltinSP("log_odds_flip", typed_nr(LogOddsBernoulliOutputPSP(),
  [t.NumberType()], t.BoolType()))

registerBuiltinSP("log_odds_bernoulli", typed_nr(LogOddsBernoulliOutputPSP(),
  [t.NumberType()], t.IntegerType()))


class BinomialOutputPSP(DiscretePSP):
  def simulate(self, args):
    (n, p) = args.operandValues()
    return args.np_prng().binomial(n, p)

  def logDensity(self, val, args):
    (n,p) = args.operandValues()
    return scipy.stats.binom.logpmf(val,n,p)

  def enumerateValues(self, args):
    (n,p) = args.operandValues()
    if p == 1:
      return [n]
    elif p == 0:
      return [0]
    else:
      return [i for i in range(int(n)+1)]

  def description(self, name):
    return '  %s(n, p) simulates flipping n Bernoulli trials independently '\
      'with probability p and returns the total number of successes.' % name


registerBuiltinSP("binomial", typed_nr(BinomialOutputPSP(),
  [t.CountType(), t.ProbabilityType()], t.CountType()))


class CategoricalOutputPSP(DiscretePSP):
  # (categorical ps outputs)
  def simulate(self, args):
    vals = args.operandValues()
    if len(vals) == 1: # Default values to choose from
      return simulateCategorical(vals[0], args.np_prng(),
        [VentureInteger(i) for i in range(len(vals[0]))])
    else:
      if len(vals[0]) != len(vals[1]):
        raise VentureValueError("Categorical passed different length arguments.")
      ps, os = vals
      return simulateCategorical(ps, args.np_prng(), os)

  def logDensity(self, val, args):
    vals = args.operandValues()
    if len(vals) == 1: # Default values to choose from
      return logDensityCategorical(val, vals[0],
        [VentureInteger(i) for i in range(len(vals[0]))])
    else:
      return logDensityCategorical(val,*vals)

  def enumerateValues(self, args):
    vals = args.operandValues()
    indexes = [i for i, p in enumerate(vals[0]) if p > 0]
    if len(vals) == 1:
      return indexes
    else:
      return [vals[1][i] for i in indexes]

  def description(self, name):
    return '  %s(weights, objects) samples a categorical with the given '\
      'weights. In the one argument case, returns the index of the chosen '\
      'option as an integer; in the two argument case returns the item at that '\
      'index in the second argument. It is an error if the two arguments '\
      'have different length.' % name


registerBuiltinSP("categorical", typed_nr(CategoricalOutputPSP(),
  [t.SimplexType(), t.ArrayType()], t.AnyType(), min_req_args=1))


class UniformDiscreteOutputPSP(DiscretePSP):
  def simulate(self, args):
    vals = args.operandValues()
    if vals[1] <= vals[0]:
      raise VentureValueError("uniform_discrete called on invalid range "\
        "(%d,%d)" % (vals[0],vals[1]))
    return args.py_prng().randrange(*vals)

  def logDensity(self, val, args):
    a,b = args.operandValues()
    if a <= val and val < b:
      return -math.log(b-a)
    else:
      return extendedLog(0.0)

  def enumerateValues(self, args):
    return range(*[int(x) for x in args.operandValues()])

  def description(self, name):
    return '  %s(start, end) samples a uniform discrete on the '\
      '(start, start + 1, ..., end - 1)' % name


registerBuiltinSP("uniform_discrete", typed_nr(UniformDiscreteOutputPSP(),
  [t.IntegerType(), t.IntegerType()], t.IntegerType()))


class PoissonOutputPSP(DiscretePSP):
  def simulate(self, args):
    (lam,) = args.operandValues()
    return args.np_prng().poisson(lam=lam)

  def logDensity(self, val, args):
    return scipy.stats.poisson.logpmf(val, args.operandValues()[0])

  def description(self, name):
    return '  %s(mu) samples a Poisson with rate mu' % name


registerBuiltinSP("poisson", typed_nr(PoissonOutputPSP(),
  [t.PositiveType()], t.CountType()))


### Collapsed Beta Bernoulli
class SuffBernoulliSPAux(SPAux):
  def __init__(self):
    self.yes = 0.0
    self.no = 0.0

  def copy(self):
    aux = SuffBernoulliSPAux()
    aux.yes = self.yes
    aux.no = self.no
    return aux

  v_type = t.HomogeneousListType(t.NumberType())

  def asVentureValue(self):
    return SuffBernoulliSPAux.v_type.asVentureValue([self.yes, self.no])

  @staticmethod
  def fromVentureValue(val):
    aux = SuffBernoulliSPAux()
    (aux.yes, aux.no) = SuffBernoulliSPAux.v_type.asPython(val)
    return aux

  def cts(self):
    return [self.yes,self.no]


class SuffBernoulliSP(SP):
  def constructSPAux(self):
    return SuffBernoulliSPAux()

  def show(self,spaux):
    return spaux.cts()


class MakerCBetaBernoulliOutputPSP(DeterministicMakerAAAPSP):
  def simulate(self, args):
    (alpha, beta) = args.operandValues()
    output = TypedPSP(CBetaBernoulliOutputPSP(alpha, beta),
      SPType([], t.BoolType()))
    return VentureSPRecord(SuffBernoulliSP(NullRequestPSP(), output))

  def description(self, name):
    return '  %s(alpha, beta) returns a collapsed Beta Bernoulli sampler with '\
      'pseudocounts alpha (for true) and beta (for false). While this  '\
      'procedure itself is deterministic, the returned sampler is stochastic.'\
      % name

  def gradientOfLogDensityOfData(self, aux, args):
    (alpha, beta) = args.operandValues()
    [ctY, ctN] = aux.cts()
    trues = ctY + alpha
    falses = ctN + beta
    numerator = scipy.special.digamma([trues, falses]) - scipy.special.digamma(trues + falses)
    denominator = scipy.special.digamma([alpha, beta]) - scipy.special.digamma(alpha + beta)
    return numerator - denominator

  def madeSpLogDensityOfDataBound(self, _aux):
    # Observations are discrete, so the logDensityOfData is bounded by 0.
    # Improving this bound is Github issue #468.
    return 0

class CBetaBernoulliOutputPSP(DiscretePSP):
  def __init__(self, alpha, beta):
    assert isinstance(alpha, float)
    assert isinstance(beta, float)
    self.alpha = alpha
    self.beta = beta

  def incorporate(self, value, args):
    spaux = args.spaux()
    if value: # I produced true
      spaux.yes += 1
    else: # I produced false
      spaux.no += 1

  def unincorporate(self, value, args):
    spaux = args.spaux()
    if value: # I produced true
      spaux.yes -= 1
    else: # I produced false
      spaux.no -= 1

  def simulate(self,args):
    [ctY,ctN] = args.spaux().cts()
    weight = (self.alpha + ctY) / (self.alpha + ctY + self.beta + ctN)
    return args.py_prng().random() < weight

  def logDensity(self,value,args):
    [ctY,ctN] = args.spaux().cts()
    weight = (self.alpha + ctY) / (self.alpha + ctY + self.beta + ctN)
    if value is True:
      return math.log(weight)
    else:
      return math.log1p(-weight)

  def logDensityOfData(self,aux):
    [ctY,ctN] = aux.cts()
    trues = ctY + self.alpha
    falses = ctN + self.beta
    numerator = scipy.special.betaln(trues,falses)
    denominator = scipy.special.betaln(self.alpha,self.beta)
    return numerator - denominator


registerBuiltinSP("make_beta_bernoulli", typed_nr(MakerCBetaBernoulliOutputPSP(),
  [t.PositiveType(), t.PositiveType()], SPType([], t.BoolType())))


#### Uncollapsed AAA Beta Bernoulli
class MakerUBetaBernoulliOutputPSP(RandomPSP):
  def childrenCanAAA(self):
    return True

  def getAAALKernel(self):
    return UBetaBernoulliAAALKernel(self)

  def simulate(self,args):
    (alpha, beta) = args.operandValues()
    weight = args.np_prng().beta(a=alpha, b=beta)
    output = TypedPSP(SuffBernoulliOutputPSP(weight), SPType([], t.BoolType()))
    return VentureSPRecord(SuffBernoulliSP(NullRequestPSP(), output))

  def logDensity(self,value,args):
    (alpha, beta) = args.operandValues()
    assert isinstance(value,VentureSPRecord)
    assert isinstance(value.sp,SuffBernoulliSP)
    coinWeight = value.sp.outputPSP.psp.weight
    return scipy.stats.beta.logpdf(coinWeight,alpha,beta)

  def marginalLogDensityOfData(self, aux, args):
    (alpha, beta) = args.operandValues()
    return CBetaBernoulliOutputPSP(alpha, beta).logDensityOfData(aux)

  def gradientOfLogDensityOfData(self, aux, args):
    return MakerCBetaBernoulliOutputPSP().gradientOfLogDensityOfData(aux, args)

  def madeSpLogDensityOfDataBound(self, aux):
    return MakerCBetaBernoulliOutputPSP().madeSpLogDensityOfDataBound(aux)

  def description(self,name):
    return '  %s(alpha, beta) returns an uncollapsed Beta Bernoulli sampler '\
      'with pseudocounts alpha (for true) and beta (for false).' % name


class UBetaBernoulliAAALKernel(PosteriorAAALKernel):
  def simulate(self, _trace, args):
    (alpha, beta) = args.operandValues()
    madeaux = args.madeSPAux()
    [ctY,ctN] = madeaux.cts()
    new_weight = args.np_prng().beta(a=(alpha + ctY), b=(beta + ctN))
    output = TypedPSP(SuffBernoulliOutputPSP(new_weight), SPType([],
      t.BoolType()))
    return VentureSPRecord(SuffBernoulliSP(NullRequestPSP(), output), madeaux)


class SuffBernoulliOutputPSP(DiscretePSP):
  def __init__(self,weight):
    self.weight = weight

  def incorporate(self, value, args):
    spaux = args.spaux()
    if value: # I produced true
      spaux.yes += 1
    else: # I produced false
      spaux.no += 1

  def unincorporate(self, value, args):
    spaux = args.spaux()
    if value: # I produced true
      spaux.yes -= 1
    else: # I produced false
      spaux.no -= 1

  def simulate(self, args):
    return args.py_prng().random() < self.weight

  def logDensity(self, value, _args):
    if value is True:
      return math.log(self.weight)
    else:
      return math.log1p(-self.weight)

  def logDensityOfData(self, aux):
    [ctY, ctN] = aux.cts()
    term1 = ctY * math.log(self.weight) if ctY > 0 else 0
    term2 = ctN * math.log1p(-self.weight) if ctN > 0 else 0
    return term1 + term2


registerBuiltinSP("make_uc_beta_bernoulli",
  typed_nr(MakerUBetaBernoulliOutputPSP(),
  [t.PositiveType(), t.PositiveType()], SPType([], t.BoolType())))


#### Non-conjugate AAA bernoulli
class MakerSuffBernoulliOutputPSP(DeterministicMakerAAAPSP):
  def simulate(self, args):
    weight = args.operandValues()[0]
    # The made SP is the same as in the conjugate case: flip coins
    # based on an explicit weight, and maintain sufficient statistics.
    output = TypedPSP(SuffBernoulliOutputPSP(weight), SPType([], t.BoolType()))
    return VentureSPRecord(SuffBernoulliSP(NullRequestPSP(), output))

  def description(self,name):
    return '  %s(weight) returns a Bernoulli sampler (weighted coin) with '\
      'given weight. The latter maintains application statistics sufficient '\
      'to absorb changes to the weight in O(1) time (without traversing all '\
      ' the applications).' % name

  def gradientOfLogDensityOfData(self, aux, args):
    '''The derivatives with respect to the args of the log density of the counts
    collected by the made SP.'''
    weight = args.operandValues()[0]
    [ctY,ctN] = aux.cts()
    return [float(ctY) / weight - float(ctN) / (1 - weight)]

  def madeSpLogDensityOfDataBound(self, _aux):
    return 0


registerBuiltinSP("make_suff_stat_bernoulli",
  typed_nr(MakerSuffBernoulliOutputPSP(),
  [t.NumberType()], SPType([], t.BoolType())))


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
    if y.equal(x):
      return 0
    return epsilon

  def logDensityBound(self, _y, _args):
    return 0

  def description(self, _name):
    return 'Force a variable to be treated as random even though its value is '\
      'known. This deterministically returns the first argument when '\
      'simulated, but is willing to pretend to be able to stochastically '\
      'return any object. The second argument, if given, is the penalty '\
      '(in log space) for a mismatch. If not given, taken to be -infinity.'


registerBuiltinSP("exactly", typed_nr(ExactlyOutputPSP(),
  [t.AnyType(), t.NumberType()], t.AnyType(), min_req_args=1))


# SP for Poisson, maintaining sufficient statistics.
class SuffPoissonSP(SP):
  def constructSPAux(self):
    return SuffPoissonSPAux()

  def show(self,spaux):
    return self.outputPSP.psp.show(spaux)


# SPAux for Poisson. The sufficent statistics for N observations are
# ctN (number of observations) and xsum (sum of the observations).
class SuffPoissonSPAux(SPAux):
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
    return SuffPoissonSPAux.v_type.asVentureValue([self.xsum, self.ctN])

  @staticmethod
  def fromVentureValue(val):
    aux = SuffPoissonSPAux()
    (aux.xsum, aux.ctN) = SuffPoissonSPAux.v_type.asPython(val)
    return aux

  def cts(self):
    return [self.xsum, self.ctN]


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

  def simulate(self, args):
    return args.np_prng().poisson(lam=self.mu)

  def logDensity(self, value, _args):
    return scipy.stats.poisson.logpmf(value, mu=self.mu)

  def logDensityOfData(self, aux):
    # Returns log P(counts|mu) because log P(xs|mu) cannot be computed
    # from the counts alone.  This is ok because the difference does
    # not depend on mu, and the 0 upper bound still applies.

    # http://www.stat.cmu.edu/~larry/=stat705/Lecture5.pdf#page=3
    # comments that the total is distributed as poisson(ctN * mu)
    [xsum, ctN] = aux.cts()
    return scipy.stats.poisson.logpmf(xsum, mu = ctN * self.mu)

  def show(self, spaux):
    return OrderedDict([
      ('type', 'suff_stat_poisson'),
      ('mu', self.mu),
      ('ctN', spaux.ctN),
      ('xsum', spaux.xsum),
    ])


# Uncollapsed Gamma Poisson PSP.
class UGammaPoissonOutputPSP(SuffPoissonOutputPSP):
  def __init__(self, mu, alpha, beta):
    SuffPoissonOutputPSP.__init__(self, mu)
    self.alpha = alpha
    self.beta = beta

  def show(self, spaux):
    return OrderedDict([
      ('type', 'uc_gamma_poisson'),
      ('mu', self.mu),
      ('alpha', self.alpha),
      ('beta', self.beta),
      ('ctN', spaux.ctN),
      ('xsum', spaux.xsum),
    ])


# Collapsed Gamma Poisson PSP.
class CGammaPoissonOutputPSP(DiscretePSP):
  def __init__(self, alpha, beta):
    assert isinstance(alpha, float)
    assert isinstance(beta, float)
    self.alpha = alpha
    self.beta = beta

  def updatedParams(self, aux):
    [xsum, ctN] = aux.cts()
    alpha_n = self.alpha + xsum
    beta_n = self.beta + ctN
    return (alpha_n, beta_n)

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
    (alpha_n, beta_n) = self.updatedParams(args.spaux())
    return args.np_prng().negative_binomial(n=alpha_n, p=(beta_n)/(beta_n+1))

  def logDensity(self, value, args):
    (alpha_n, beta_n) = self.updatedParams(args.spaux())
    return scipy.stats.nbinom.logpmf(value, n=alpha_n, p=(beta_n)/(beta_n+1))

  def logDensityOfData(self, aux):
    # The marginal loglikelihood of the data p(D) under the prior.
    # http://seor.gmu.edu/~klaskey/SYST664/Bayes_Unit3.pdf#page=42
    # Note that our parameterization is different than the reference, since
    # self.beta = 1 / ref.beta
    [xsum, ctN] = aux.cts()
    return scipy.special.gammaln(self.alpha + xsum) - \
      scipy.special.gammaln(self.alpha) + self.alpha * math.log(self.beta) - \
      (self.alpha + xsum) * math.log(self.beta + ctN)

  def show(self, spaux):
    (alpha_n, beta_n) = self.updatedParams(spaux)
    return OrderedDict([
      ('type', 'gamma_poisson'),
      ('alpha_0', self.alpha),
      ('beta_0', self.beta),
      ('alpha_n', alpha_n),
      ('beta_n', beta_n),
      ('ctN', spaux.ctN),
      ('xsum', spaux.xsum),
    ])


class MakerCGammaPoissonOutputPSP(DeterministicMakerAAAPSP):
# Maker for Collapsed Gamma Poisson
  def simulate(self, args):
    (alpha, beta) = args.operandValues()
    output = TypedPSP(CGammaPoissonOutputPSP(alpha, beta),
      SPType([], t.CountType()))
    return VentureSPRecord(SuffPoissonSP(NullRequestPSP(), output))

  def description(self, name):
    return '  %s(alpha, beta) returns a collapsed Gamma Poisson sampler. '\
      'While this procedure itself is deterministic, the returned sampler '\
      'is stochastic.' % name


registerBuiltinSP("make_gamma_poisson", typed_nr(MakerCGammaPoissonOutputPSP(),
  [t.PositiveType(), t.PositiveType()], SPType([], t.CountType())))


class MakerUGammaPoissonOutputPSP(DiscretePSP):
# Maker for Uncollapsed AAA GammaPoisson
  def childrenCanAAA(self):
    return True

  def getAAALKernel(self):
    return UGammaPoissonAAALKernel(self)

  def simulate(self, args):
    (alpha, beta) = args.operandValues()
    mu = args.np_prng().gamma(shape=alpha, scale=1./beta)
    output = TypedPSP(UGammaPoissonOutputPSP(mu, alpha, beta),
      SPType([], t.CountType()))
    return VentureSPRecord(SuffPoissonSP(NullRequestPSP(), output))

  def logDensity(self, value, args):
    assert isinstance(value,VentureSPRecord)
    assert isinstance(value.sp,SuffPoissonSP)
    (alpha, beta) = args.operandValues()
    mu = value.sp.outputPSP.psp.mu
    return scipy.stats.gamma.logpdf(mu, a=alpha, scale=1./beta)

  def marginalLogDensityOfData(self, aux, args):
    (alpha, beta) = args.operandValues()
    return CGammaPoissonOutputPSP(alpha, beta).logDensityOfData(aux)

  def description(self, name):
    return '  %s(alpha, beta) returns an uncollapsed Gamma Poisson sampler.'\
      % name

class UGammaPoissonAAALKernel(PosteriorAAALKernel):
  def simulate(self, _trace, args):
    madeaux = args.madeSPAux()
    [xsum, ctN] = madeaux.cts()
    (alpha, beta) = args.operandValues()
    new_alpha = alpha + xsum
    new_beta = beta + ctN
    new_mu = args.np_prng().gamma(shape=(alpha + xsum), scale=1./new_beta)
    output = TypedPSP(UGammaPoissonOutputPSP(new_mu, new_alpha, new_beta),
      SPType([], t.CountType()))
    return VentureSPRecord(SuffPoissonSP(NullRequestPSP(), output), madeaux)


registerBuiltinSP("make_uc_gamma_poisson",
  typed_nr(MakerUGammaPoissonOutputPSP(), [t.PositiveType(), t.PositiveType()],
  SPType([], t.CountType())))


class MakerSuffPoissonOutputPSP(DeterministicMakerAAAPSP):
# Non-conjugate AAA Poisson

  def simulate(self, args):
    mu = args.operandValues()[0]
    output = TypedPSP(SuffPoissonOutputPSP(mu), SPType([], t.CountType()))
    return VentureSPRecord(SuffPoissonSP(NullRequestPSP(), output))

  def description(self,name):
    return '  %s(mu) returns Poisson sampler with given mu. '\
      'While this procedure itself is deterministic, the returned sampler '\
      'is stochastic. The latter maintains application statistics sufficient '\
      'to absorb changes to the weight in O(1) time (without traversing all '\
      'the applications.' % name

  def gradientOfLogDensityOfData(self, aux, args):
    '''The derivatives with respect to the args of the log density of the counts
    collected by the made SP.'''
    mu = args.operandValues()[0]
    [xsum, ctN] = aux.cts()
    return [-ctN + xsum / mu]

  def madeSpLogDensityOfDataBound(self, _aux):
    return 0

registerBuiltinSP("make_suff_stat_poisson",
  typed_nr(MakerSuffPoissonOutputPSP(), [t.PositiveType()], SPType([],
  t.CountType())))
