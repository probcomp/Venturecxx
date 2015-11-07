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

from ..lite.exception import VentureError
from venture.exception import VentureException
from ..lite import types as t
from ..lite import value as vv
from ..lite import env
from ..lite import address as addr
from ..lite.sp import VentureSPRecord
from ..lite import builtin

import node
import evaluator

class Trace(object):

  def __init__(self):
    self.results = {}
    self.env = env.VentureEnvironment()
    for name, val in builtin.builtInValues().iteritems():
      self.bindPrimitiveName(name, val)
    for name, sp in builtin.builtInSPs().iteritems():
      self.bindPrimitiveSP(name, sp)
    self.sealEnvironment() # New frame so users can shadow globals

  def sealEnvironment(self):
    self.env = env.VentureEnvironment(self.env)

  def extractRaw(self, id):
    return self.results[id]

  def extractValue(self, id):
    return self.extractRaw(id).asStackDict(self)

  def eval(self, id, exp):
    assert id not in self.results
    py_exp = t.ExpressionType().asPython(vv.VentureValue.fromStackDict(exp))
    val = evaluator.eval(addr.Address(addr.List(id)), py_exp, self.env)
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
    if self.boundInGlobalEnv(sym):
      # No problems with overwrites in the untraced setting.
      self.unbindInGlobalEnv(sym)
    try:
      self.env.addBinding(sym, node.Node(id, self.results[id]))
    except VentureError as e:
      raise VentureException("invalid_argument", message=e.message, argument="symbol")

  def unbindInGlobalEnv(self, sym): self.env.removeBinding(sym)

  def boundInGlobalEnv(self, sym): return self.env.symbolBound(sym)
