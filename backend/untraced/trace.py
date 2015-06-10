from ..lite import types as t
from ..lite import value as vv
from ..lite import env
from ..lite import address as addr
from ..lite.sp import VentureSPRecord
from ..lite import builtin

import evaluator

class Trace(object):

  def __init__(self):
    self.results = {}
    self.env = env.VentureEnvironment()
    for name, val in builtin.builtInValues().iteritems():
      self.bindPrimitiveName(name, val)
    for name, sp in builtin.builtInSPs().iteritems():
      self.bindPrimitiveSP(name, sp)
    self.env = env.VentureEnvironment(self.env) # New frame so users can shadow globals

  def extractRaw(self, id):
    return self.results[id]

  def extractValue(self, id):
    return self.extractRaw(id).asStackDict(self)

  def eval(self, id, exp):
    assert id not in self.results
    py_exp = t.ExpressionType().asPython(vv.VentureValue.fromStackDict(exp))
    self.results[id] = evaluator.eval(addr.Address(addr.List(id)), py_exp, self.env)

  def bindPrimitiveName(self, name, val):
    self.env.addBinding(name, val)

  def bindPrimitiveSP(self, name, sp):
    # TODO Mess with SPRecords and SPRefs properly
    spVal = VentureSPRecord(sp)
    self.env.addBinding(name, spVal)

  def boundInGlobalEnv(self, sym): return self.env.symbolBound(sym)
