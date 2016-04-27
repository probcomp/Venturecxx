import math

from venture.lite.address import Address
from venture.lite.address import List
from venture.lite.env import VentureEnvironment
from venture.lite.node import OutputNode
from venture.lite.omegadb import OmegaDB
from venture.lite.sp import SPFamilies
from venture.lite.trace import Trace as LiteTrace

from venture.mite.builtin import builtInSPs
from venture.mite.builtin import builtInValues
from venture.mite.evaluator import EvalContext, RestoreContext
from venture.mite.sp import Args

class Trace(LiteTrace):
  def __init__(self):
    self.globalEnv = VentureEnvironment()
    for name, val in builtInValues().iteritems():
      self.bindPrimitiveName(name, val)
    for name, sp in builtInSPs().iteritems():
      self.bindPrimitiveSP(name, sp)
    self.sealEnvironment() # New frame so users can shadow globals

    self.unpropagatedObservations = {}
    self.families = {}

  def bindPrimitiveSP(self, name, sp):
    spNode = self.createConstantNode(None, sp)
    EvalContext(self).processMadeSP(spNode)
    self.globalEnv.addBinding(name, spNode)

  ## Internal interface to eval/regen

  def createApplicationNodes(self, address, operatorNode, operandNodes, env):
    # Request nodes don't exist now, so just create a singular node.
    outputNode = OutputNode(address, operatorNode, operandNodes, None, env)
    self.addChildAt(operatorNode, outputNode)
    for operandNode in operandNodes:
      self.addChildAt(operandNode, outputNode)
    return outputNode

  def argsAt(self, node, context=None):
    return Args(self, node, context=context)

  def madeSPAt(self, node):
    # SPs and SPRecords are the same now.
    return self.madeSPRecordAt(node)

  def madeSPFamiliesAt(self, node):
    # TODO: decide whether to re-introduce SP records so we don't have
    # to do this hack
    sp = self.madeSPRecordAt(node)
    if not hasattr(sp, 'requestedFamilies'):
      sp.requestedFamilies = SPFamilies()
    assert isinstance(sp.requestedFamilies, SPFamilies)
    return sp.requestedFamilies

  ## External interface to engine

  def eval(self, id, exp):
    assert id not in self.families
    (w, self.families[id]) = EvalContext(self).evalFamily(
      Address(List(id)), self.unboxExpression(exp), self.globalEnv)
    # forward evaluation should not produce a weight
    # (is this always true?)
    assert w == 0

  def uneval(self, id):
    assert id in self.families
    w = EvalContext(self).unevalFamily(self.families[id])
    assert w == 0
    del self.families[id]

  def makeConsistent(self):
    weight = 0
    for node, val in self.unpropagatedObservations.iteritems():
      # appNode = self.getConstrainableNode(node)
      # scaffold = constructScaffold(self, [set([appNode])])
      # rhoWeight, _ = detachAndExtract(self, scaffold)
      # scaffold.lkernels[appNode] = DeterministicLKernel(self.pspAt(appNode), val)
      # xiWeight = regenAndAttach(self, scaffold, False, OmegaDB(), {})
      node.observe(val)
      weight += EvalContext(self).constrain(node, node.observedValue)
    self.unpropagatedObservations.clear()
    if not math.isinf(weight) and not math.isnan(weight):
      return weight
    else:
      # If one observation made the state inconsistent, the rhoWeight
      # of another might conceivably be infinite, possibly leading to
      # a nan weight.  I want to normalize these to indicating that
      # the resulting state is impossible.
      return float("-inf")

  # use instead of makeConsistent when restoring a trace
  def registerConstraints(self):
    for node, val in self.unpropagatedObservations.iteritems():
      # appNode = self.getConstrainableNode(node)
      node.observe(val)
      EvalContext(self).constrain(node, node.observedValue)
    self.unpropagatedObservations.clear()

  def unobserve(self, id):
    node = self.families[id]
    if node.isObservation:
      weight = EvalContext(self).unconstrain(node)
      node.isObservation = False
    else:
      assert node in self.unpropagatedObservations
      del self.unpropagatedObservations[node]
      weight = 0
    return weight

  def primitive_infer(self, exp):
    print 'primitive_infer', exp
    return None

  def select(self, scope, block):
    if scope.getSymbol() == 'default' and block.getSymbol() == 'all':
      return 'all'
    print 'select', scope, block
    return None

  def just_detach(self, scaffold):
    if scaffold == 'all':
      return self.detach_all()
    print 'detach', scaffold
    return 0, None

  def just_regen(self, scaffold):
    if scaffold == 'all':
      return self.regen_all()
    print 'regen', scaffold
    return 0

  def just_restore(self, scaffold, rhoDB):
    if scaffold == 'all':
      return self.restore_all(rhoDB)
    print 'restore', scaffold, rhoDB
    return 0

  ## Global detach/regen by replaying all directives (as in serialize)

  def detach_all(self):
    weight = 0
    rhoDB = OmegaDB()
    for id in reversed(sorted(self.families)):
      node = self.families[id]
      if node.isObservation:
        weight += RestoreContext(self, rhoDB).unconstrain(self.families[id])
      RestoreContext(self, rhoDB).unevalFamily(node)
    return weight, rhoDB

  def regen_all(self):
    weight = 0
    rhoDB = OmegaDB()
    for id in sorted(self.families):
      node = self.families[id]
      EvalContext(self).restore(node)
      if node.isObservation:
        weight += RestoreContext(self, rhoDB).constrain(node, node.observedValue)
    return weight

  def restore_all(self, rhoDB):
    weight = 0
    for id in sorted(self.families):
      node = self.families[id]
      RestoreContext(self, rhoDB).restore(node)
      if node.isObservation:
        weight += RestoreContext(self, rhoDB).constrain(node, node.observedValue)
    return weight

  ## Serialization interface

  def makeSerializationDB(self, values=None, skipStackDictConversion=False):
    db = OmegaDB()
    if values is not None:
      if not skipStackDictConversion:
        values = {key: self.unboxValue(value) for key, value in values.items()}
      db.values.update(values)
    return db

  def dumpSerializationDB(self, db, skipStackDictConversion=False):
    values = db.values
    if not skipStackDictConversion:
      values = {key: self.boxValue(value) for key, value in values.items()}
    return values

  def unevalAndExtract(self, id, db):
    # leaves trace in an inconsistent state. use restore afterward
    assert id in self.families
    RestoreContext(self, db).unevalFamily(self.families[id])

  def restore(self, id, db):
    assert id in self.families
    RestoreContext(self, db).restore(self.families[id])

  def evalAndRestore(self, id, exp, db):
    assert id not in self.families
    (w, self.families[id]) = RestoreContext(self, db).evalFamily(
      Address(List(id)), self.unboxExpression(exp), self.globalEnv)
    assert w == 0
