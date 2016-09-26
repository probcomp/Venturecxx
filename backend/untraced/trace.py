# Copyright (c) 2015 MIT Probabilistic Computing Project.
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
import numpy.random as npr

from venture.exception import VentureException
from venture.lite import address as addr
from venture.lite import builtin
from venture.lite import env
from venture.lite import types as t
from venture.lite import value as vv
from venture.lite.exception import VentureError
from venture.lite.sp import VentureSPRecord
import venture.untraced.evaluator as evaluator
import venture.untraced.node as node

class Trace(object):

  def __init__(self, seed):
    self.results = {}
    self.env = env.VentureEnvironment()
    for name, val in builtin.builtInValues().iteritems():
      self.bindPrimitiveName(name, val)
    for name, sp in builtin.builtInSPs().iteritems():
      self.bindPrimitiveSP(name, sp)
    self.sealEnvironment() # New frame so users can shadow globals

    assert seed is not None
    rng = random.Random(seed)
    self.np_rng = npr.RandomState(rng.randint(1, 2**31 - 1))
    self.py_rng = random.Random(rng.randint(1, 2**31 - 1))

  def sealEnvironment(self):
    self.env = env.VentureEnvironment(self.env)

  def extractRaw(self, id):
    return self.results[id]

  def extractValue(self, id):
    return self.extractRaw(id).asStackDict(self)

  def eval(self, id, exp):
    assert id not in self.results
    py_exp = t.ExpressionType().asPython(vv.VentureValue.fromStackDict(exp))
    rng = self.py_rng
    val = evaluator.eval(addr.directive_address(id), py_exp, self.env, rng)
    assert isinstance(val, vv.VentureValue)
    self.results[id] = val

  def uneval(self, id):
    # Not much to do here
    assert id in self.results
    del self.results[id]

  def bindPrimitiveName(self, name, val):
    self.env.addBinding(name, node.Node(None, val))

  def bindPrimitiveSP(self, name, sp):
    # TODO Mess with SPRecords and SPRefs properly
    spVal = VentureSPRecord(sp)
    self.env.addBinding(name, node.Node(None, spVal))

  def bindInGlobalEnv(self, sym, id):
    if sym in self.env.frame:
      # No problems with overwrites in the untraced setting
      del self.env.frame[sym]
    try:
      self.env.addBinding(sym, node.Node(id, self.results[id]))
    except VentureError as e:
      raise VentureException("invalid_argument", message=e.message, argument="symbol")

  def unbindInGlobalEnv(self, sym): self.env.removeBinding(sym)

  def boundInGlobalEnv(self, sym): return self.env.symbolBound(sym)
