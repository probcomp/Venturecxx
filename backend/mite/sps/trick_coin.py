from __future__ import division

import numpy as np
from scipy.special import betaln

import venture.lite.types as t

from venture.mite.sp import SimulationSP
from venture.mite.sp_registry import registerBuiltinSP

class TrickCoinSP(SimulationSP):
  """A tricky coin.

  Equivalent to this model:
  (let ((is_fair (flip p_fair)))
   (if is_fair
       (make_beta_bernoulli a_fair a_fair)
       (make_beta_bernoulli a_unfair a_unfair)))
  """

  def __init__(self, p_fair, a_fair, a_unfair):
    self.p_fair = p_fair
    self.p_unfair = 1 - p_fair
    self.a_fair = a_fair
    self.a_unfair = a_unfair
    self.n_heads = 0
    self.n_tails = 0

  def predictive_prob(self):
    fair_heads = self.a_fair + self.n_heads
    fair_tails = self.a_fair + self.n_tails
    fair_predictive = fair_heads / (fair_heads + fair_tails)
    fair_likelihood = betaln(fair_heads, fair_tails) - betaln(self.a_fair, self.a_fair)

    unfair_heads = self.a_unfair + self.n_heads
    unfair_tails = self.a_unfair + self.n_tails
    unfair_predictive = unfair_heads / (unfair_heads + unfair_tails)
    unfair_likelihood = betaln(unfair_heads, unfair_tails) - betaln(self.a_unfair, self.a_unfair)

    max_likelihood = max(fair_likelihood, unfair_likelihood)
    fair_weight = self.p_fair * np.exp(fair_likelihood - max_likelihood)
    unfair_weight = self.p_unfair * np.exp(unfair_likelihood - max_likelihood)

    numerator = fair_weight * fair_predictive + unfair_weight * unfair_predictive
    denominator = fair_weight + unfair_weight

    return numerator / denominator

  def simulate(self, args):
    prob = self.predictive_prob()
    return t.Bool.asVentureValue(args.py_prng().random() < prob)

  def logDensity(self, value, args):
    prob = self.predictive_prob()
    if t.Bool.asPython(value):
      return np.log(prob)
    else:
      return np.log1p(-prob)

  def incorporate(self, value, args):
    if t.Bool.asPython(value):
      self.n_heads += 1
    else:
      self.n_tails += 1

  def unincorporate(self, value, args):
    if t.Bool.asPython(value):
      self.n_heads -= 1
    else:
      self.n_tails -= 1

class MakeTrickCoinSP(SimulationSP):
  def simulate(self, args):
    arg_types = [t.Probability, t.Number, t.Number]
    [p_fair, a_fair, a_unfair] = [
      arg_type.asPython(value)
      for arg_type, value in zip(arg_types, args.operandValues())]
    return TrickCoinSP(p_fair, a_fair, a_unfair)

registerBuiltinSP("make_trick_coin", MakeTrickCoinSP())
