from venture.lite.builtin import builtInSPs
from venture.lite.psp import TypedPSP
from venture.lite.sp import VentureSPRecord, SPType
import venture.lite.types as t

from venture.mite.sp import (SimpleRandomSPWrapper,
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

  return spsList
