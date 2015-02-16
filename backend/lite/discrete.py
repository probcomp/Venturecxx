import random
import math
import scipy
import scipy.special
from utils import extendedLog, simulateCategorical, logDensityCategorical
from psp import DeterministicPSP, NullRequestPSP, RandomPSP, TypedPSP
from sp import SP, SPAux, VentureSPRecord, SPType
from lkernel import LKernel
from value import VentureAtom, BoolType # BoolType is metaprogrammed pylint:disable=no-name-in-module
from exception import VentureValueError

class DiscretePSP(RandomPSP):
  def logDensityBound(self, _x, _args): return 0

class BernoulliOutputPSP(DiscretePSP):
  def simulate(self,args):
    p = args.operandValues[0] if args.operandValues else 0.5
    return random.random() < p

  def logDensity(self,val,args):
    p = args.operandValues[0] if args.operandValues else 0.5
    if val: return extendedLog(p)
    else: return extendedLog(1 - p)

  def gradientOfLogDensity(self, val, args):
    p = args.operandValues[0] if args.operandValues else 0.5
    deriv = 1/p if val else -1 / (1 - p)
    return (0, [deriv])

  def enumerateValues(self,args):
    p = args.operandValues[0] if args.operandValues else 0.5
    if p == 1: return [True]
    elif p == 0: return [False]
    else: return [True,False]

  def description(self,name):
    return "  (%s p) returns true with probability p and false otherwise.  If omitted, p is taken to be 0.5." % name

class LogBernoulliOutputPSP(DiscretePSP):
  def simulate(self,args):
    logp = args.operandValues[0]
    return math.log(random.random()) < logp

  def logDensity(self,val,args):
    logp = args.operandValues[0]
    if val: return logp
    else: return extendedLog(1 - math.exp(logp))

  def gradientOfLogDensity(self, val, args):
    logp = args.operandValues[0]
    deriv = 1 if val else 1 / (1 - math.exp(-logp))
    return (0, [deriv])

  def enumerateValues(self,args):
    logp = args.operandValues[0]
    if p == 0: return [True]
    elif p == float('-inf'): return [False]
    else: return [True,False]

  def description(self,name):
    return "  (%s p) returns true with probability exp(p) and false otherwise." % name

class BinomialOutputPSP(DiscretePSP):
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

  def description(self,name):
    return "  (%s n p) simulates flipping n Bernoulli trials independently with probability p and returns the total number of successes." % name


class CategoricalOutputPSP(DiscretePSP):
  # (categorical ps outputs)
  def simulate(self,args):
    if len(args.operandValues) == 1: # Default values to choose from
      return simulateCategorical(args.operandValues[0], [VentureAtom(i) for i in range(len(args.operandValues[0]))])
    else:
      if not len(args.operandValues[0]) == len(args.operandValues[1]):
        raise VentureValueError("Categorical passed different length arguments.")
      return simulateCategorical(*args.operandValues)

  def logDensity(self,val,args):
    if len(args.operandValues) == 1: # Default values to choose from
      return logDensityCategorical(val, args.operandValues[0], [VentureAtom(i) for i in range(len(args.operandValues[0]))])
    else:
      return logDensityCategorical(val,*args.operandValues)

  def enumerateValues(self,args):
    indexes = [i for i, p in enumerate(args.operandValues[0]) if p > 0]
    if len(args.operandValues) == 1: return indexes
    else: return [args.operandValues[1][i] for i in indexes]

  def description(self,name):
    return "  (%s weights objects) samples a categorical with the given weights.  In the one argument case, returns the index of the chosen option as an atom; in the two argument case returns the item at that index in the second argument.  It is an error if the two arguments have different length." % name

class UniformDiscreteOutputPSP(DiscretePSP):
  def simulate(self,args):
    if args.operandValues[1] <= args.operandValues[0]:
      raise VentureValueError("uniform_discrete called on invalid range (%d,%d)" % (args.operandValues[0],args.operandValues[1]))
    return random.randrange(*args.operandValues)

  def logDensity(self,val,args):
    a,b = args.operandValues
    if a <= val and val < b: return -math.log(b-a)
    else: return extendedLog(0.0)

  def enumerateValues(self,args): return range(*[int(x) for x in args.operandValues])

  def description(self,name):
    return "  (%s start end) samples a uniform discrete on the (start, start + 1, ..., end - 1)" % name

class PoissonOutputPSP(DiscretePSP):
  def simulate(self,args): return scipy.stats.poisson.rvs(args.operandValues[0])
  def logDensity(self,val,args): return scipy.stats.poisson.logpmf(val,args.operandValues[0])
  def description(self,name):
    return "  (%s lambda) samples a poisson with rate lambda" % name


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

class BetaBernoulliSP(SP):
  def constructSPAux(self): return BetaBernoulliSPAux()
  def show(self,spaux): return spaux.cts()

class MakerCBetaBernoulliOutputPSP(DeterministicPSP):
  def childrenCanAAA(self): return True

  def simulate(self,args):
    alpha = args.operandValues[0]
    beta  = args.operandValues[1]
    output = TypedPSP(CBetaBernoulliOutputPSP(alpha, beta), SPType([], BoolType()))
    return VentureSPRecord(BetaBernoulliSP(NullRequestPSP(), output))

  def description(self,name):
    return "  (%s alpha beta) returns a collapsed beta bernoulli sampler with pseudocounts alpha (for true) and beta (for false).  While this procedure itself is deterministic, the returned sampler is stochastic." % name

class CBetaBernoulliOutputPSP(DiscretePSP):
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

class MakerUBetaBernoulliOutputPSP(DiscretePSP):
  def childrenCanAAA(self): return True
  def getAAALKernel(self): return UBetaBernoulliAAALKernel()

  def simulate(self,args):
    alpha = args.operandValues[0]
    beta  = args.operandValues[1]
    weight = scipy.stats.beta.rvs(alpha, beta)
    output = TypedPSP(UBetaBernoulliOutputPSP(weight), SPType([], BoolType()))
    return VentureSPRecord(BetaBernoulliSP(NullRequestPSP(), output))

  def logDensity(self,value,args):
    alpha = args.operandValues[0]
    beta  = args.operandValues[1]
    assert isinstance(value,VentureSPRecord)
    assert isinstance(value.sp,BetaBernoulliSP)
    coinWeight = value.sp.outputPSP.psp.weight
    return scipy.stats.beta.logpdf(coinWeight,alpha,beta)

  def description(self,name):
    return "  (%s alpha beta) returns an uncollapsed beta bernoulli sampler with pseudocounts alpha (for true) and beta (for false)." % name

class UBetaBernoulliAAALKernel(LKernel):
  def simulate(self, _trace, _oldValue, args):
    alpha = args.operandValues[0]
    beta  = args.operandValues[1]
    [ctY,ctN] = args.madeSPAux.cts()
    newWeight = scipy.stats.beta.rvs(alpha + ctY, beta + ctN)
    output = TypedPSP(UBetaBernoulliOutputPSP(newWeight), SPType([], BoolType()))
    return VentureSPRecord(BetaBernoulliSP(NullRequestPSP(), output), args.madeSPAux)
  # Weight is zero because it's simulating from the right distribution

  def weightBound(self, _trace, _newValue, _oldValue, _args): return 0

class UBetaBernoulliOutputPSP(DiscretePSP):
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

  def simulate(self, _args): return random.random() < self.weight

  def logDensity(self, value, _args):
    if value == True:
      return math.log(self.weight)
    else:
      return math.log(1-self.weight)

class ExactlyOutputPSP(RandomPSP):
  def simulate(self, args):
    x, _epsilon = args.operandValues
    return x

  def logDensity(self, y, args):
    x, epsilon = args.operandValues
    if y is x: return 0
    return epsilon

  def logDensityBound(self, _y, _args):
    return 0

  def description(self, _name):
    return """Force a variable to be treated as random even though its value is known.

This deterministically returns the first argument when simulated, but
is willing to pretend to be able to stochastically return any object.
The second argument, if given, is the penalty (in log space) for a mismatch.
If not given, taken to be -infinity. """

