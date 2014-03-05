import random
import math
import scipy
import scipy.special
from utils import simulateCategorical, logDensityCategorical
from psp import PSP, NullRequestPSP, RandomPSP, TypedPSP
from sp import VentureSP, SPAux, SPType
from lkernel import LKernel
from value import VentureAtom, BoolType # BoolType is metaprogrammed pylint:disable=no-name-in-module

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
    return "  (%s p) returns true with probability p and false otherwise.  If omitted, p is taken to be 0.5." % name

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

  def description(self,name):
    return "  (%s n p) simulates flipping n Bernoulli trials independently with probability p and returns the total number of successes." % name


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
    return "  (%s weights objects) samples a categorical with the given weights.  In the one argument case, returns the index of the chosen option as an atom; in the two argument case returns the item at that index in the second argument.  It is an error if the two arguments have different length." % name

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
    output = TypedPSP(CBetaBernoulliOutputPSP(alpha, beta), SPType([], BoolType()))
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
    output = TypedPSP(UBetaBernoulliOutputPSP(weight), SPType([], BoolType()))
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
    output = TypedPSP(UBetaBernoulliOutputPSP(newWeight), SPType([], BoolType()))
    return BetaBernoulliSP(NullRequestPSP(), output)
  # Weight is zero because it's simulating from the right distribution

  def weightBound(self, _trace, _newValue, _oldValue, _args): return 0

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

  def logDensity(self, value, _args):
    if value == True:
      return math.log(self.weight)
    else:
      return math.log(1-self.weight)
