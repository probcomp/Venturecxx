from ..lite import types as t
from ..lite import value as vv
from ..lite import env
from ..lite import address as addr

import evaluator

class Trace(object):

  def __init__(self):
    self.results = {}
    self.env = env.VentureEnvironment()

  def extractRaw(self, id):
    return self.results[id]

  def extractValue(self, id):
    return self.extractRaw(id).asStackDict(self)

  def eval(self, id, exp):
    assert id not in self.results
    py_exp = t.ExpressionType().asPython(vv.VentureValue.fromStackDict(exp))
    self.results[id] = evaluator.eval(addr.Address(addr.List(id)), py_exp, self.env)
