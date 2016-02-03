from venture.lite.builtin import builtInSPs
from venture.lite.psp import TypedPSP
from venture.lite.sp import VentureSPRecord, SPType
import venture.lite.types as t

from venture.mite.sp import (StochasticProcedure,
                             SimpleRandomSPWrapper,
                             SimpleDeterministicSPWrapper,
                             SimpleLikelihoodFreeSP)
from venture.mite.csp import make_csp

liteBuiltInSPs = builtInSPs

wrappedRandomSPs = [
  'beta',
  'flip',
]

wrappedDeterministicSPs = [
  'add',
]

from venture.lite.discrete import BetaBernoulliSPAux, CBetaBernoulliOutputPSP
class MakeBetaBernoulliSP(SimpleLikelihoodFreeSP):
  def simulate(self, args):
    [alpha, beta] = args.operandValues()
    alpha = alpha.getNumber()
    beta = beta.getNumber()
    return VentureSPRecord(SimpleRandomSPWrapper(
      TypedPSP(CBetaBernoulliOutputPSP(alpha, beta),
               SPType([], t.BoolType()))),
      BetaBernoulliSPAux())

from venture.lite.value import VentureInteger, VentureBool
from venture.lite.node import FixedValueArgs
class RepeatCoinSP(StochasticProcedure):
  def apply(self, args, constraint):
    [n, coin] = args.operandValues()
    n = n.getInteger()
    if constraint is None:
      cvals = [None] * n
    else:
      c = constraint.getInteger()
      cvals = map(VentureBool, [True] * c + [False] * (n - c))
      # TODO include binomial factor in weight?
    k = 0
    weight = 0
    for cval in cvals:
      fvargs = FixedValueArgs(args, [], [])
      result, wt = args.apply(coin, fvargs, cval)
      if result.getBool():
        k += 1
      weight += wt
    return VentureInteger(k), weight

  def unapply(self, value, args, constraint):
    [n, coin] = args.operandValues()
    n = n.getInteger()
    k = value.getInteger()
    results = map(VentureBool, [True] * k + [False] * (n - k))
    if constraint is None:
      cvals = [None] * n
    else:
      c = constraint.getInteger()
      cvals = map(VentureBool, [True] * c + [False] * (n - c))
    weight = 0
    for result, cval in zip(results, cvals):
      fvargs = FixedValueArgs(args, [], [])
      wt = args.unapply(coin, result, fvargs, cval)
      weight += wt
    return wt

def builtInSPs():
  spsList = []

  for sp in wrappedRandomSPs:
    spsList.append((sp, SimpleRandomSPWrapper(
      liteBuiltInSPs()[sp].outputPSP)))

  for sp in wrappedDeterministicSPs:
    spsList.append((sp, SimpleDeterministicSPWrapper(
      liteBuiltInSPs()[sp].outputPSP)))

  spsList.append(('make_csp', SimpleDeterministicSPWrapper(make_csp)))
  spsList.append(('make_beta_bernoulli', MakeBetaBernoulliSP()))
  spsList.append(('repeat_coin', RepeatCoinSP()))

  return spsList
