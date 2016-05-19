from __future__ import division

import numpy as np
from scipy.special import betaln

import venture.lite.range_tree as range_tree
import venture.lite.types as t
from venture.lite.utils import simulateCategorical

from venture.mite.sp import SimulationSP
from venture.mite.sp_registry import registerBuiltinSP

class SuffCatSP(SimulationSP):
  """An SP that samples from a given categorical distribution and
  collects sufficient statistics.

  Equivalent to this model:
  (lambda ()
    (categorical probs outputs))
  """

  def __init__(self, probs, outputs=None):
    self.probs = probs
    self.outputs = outputs
    self.counts = [0 for _ in probs]
    self.index_map = {}

  def apply(self, args):
    index = simulateCategorical(self.probs, args.np_prng())
    self.counts[index] += 1
    self.index_map[args.node] = index
    return self.outputs[index]

  def unapply(self, args):
    index = self.index_map.pop(args.node)
    self.counts[index] -= 1
    args.setState(args.node, index)

  def restore(self, args):
    index = args.getState(args.node)
    self.counts[index] += 1
    self.index_map[args.node] = index
    return self.outputs[index]

  def constrain(self, value, args):
    index = self.index_map.pop(args.node)
    self.counts[index] -= 1

    probs = []
    indices = []
    for i, prob in enumerate(self.probs):
      if self.outputs[i] == value:
        probs.append(prob)
        indices.append(i)

    index = simulateCategorical(probs, args.np_prng(), indices)
    self.counts[index] += 1
    self.index_map[args.node] = index

    return np.log(sum(probs)) - np.log(sum(self.probs))

  def unconstrain(self, args):
    value = args.outputValue()
    index = self.index_map.pop(args.node)
    self.counts[index] -= 1
    args.setState(args.node, index, ext="constrained index")

    probs = []
    for i, prob in enumerate(self.probs):
      if self.outputs[i] == value:
        probs.append(prob)

    index = simulateCategorical(self.probs, args.np_prng())
    self.counts[index] += 1
    self.index_map[args.node] = index

    return np.log(sum(probs)) - np.log(sum(self.probs)), self.outputs[index]

  def reconstrain(self, value, args):
    index = self.index_map.pop(args.node)
    self.counts[index] -= 1

    probs = []
    for i, prob in enumerate(self.probs):
      if self.outputs[i] == value:
        probs.append(prob)

    index = args.getState(args.node, ext="constrained index")
    self.counts[index] += 1
    self.index_map[args.node] = index

    return np.log(sum(probs)) - np.log(sum(self.probs))

  def extractStateAsVentureValue(self):
    return t.Array(t.Int).asVentureValue(self.counts)

class MakeSuffCatSP(SimulationSP):
  def simulate(self, args):
    arg_types = [t.Simplex, t.Array(t.Object)]
    [probs, outputs] = [
      arg_type.asPython(value)
      for arg_type, value in zip(arg_types, args.operandValues())]
    return SuffCatSP(probs, outputs)

registerBuiltinSP("make_suff_cat", MakeSuffCatSP())
