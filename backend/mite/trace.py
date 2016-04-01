from venture.lite.address import Address
from venture.lite.address import List
from venture.lite.env import VentureEnvironment
from venture.lite.trace import Trace as LiteTrace

from venture.mite.evaluator import evalFamily, unevalFamily

class Trace(LiteTrace):
  def __init__(self):
    self.globalEnv = VentureEnvironment()
    self.unpropagatedObservations = {}
    self.families = {}

  def eval(self, id, exp):
    assert id not in self.families
    (_, self.families[id]) = evalFamily(
      self, Address(List(id)), self.unboxExpression(exp), self.globalEnv)

  def uneval(self, id):
    assert id in self.families
    unevalFamily(self, self.families[id])
    del self.families[id]

  def makeConsistent(self):
    for node, val in self.unpropagatedObservations.iteritems():
      print 'propagate', node, val
    self.unpropagatedObservations.clear()
    return 0

  def primitive_infer(self, exp):
    print 'primitive_infer', exp
    return None

  def select(self, scope, block):
    print 'select', scope, block
    return None

  def just_detach(self, scaffold):
    print 'detach', scaffold
    return 0, None

  def just_regen(self, scaffold):
    print 'regen', scaffold
    return 0

  def just_restore(self, scaffold, rhoDB):
    print 'restore', scaffold, rhoDB
    return 0
