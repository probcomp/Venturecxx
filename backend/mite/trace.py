import math

from venture.lite.address import Address
from venture.lite.address import List
from venture.lite.env import VentureEnvironment
from venture.lite.node import OutputNode
from venture.lite.sp import SPFamilies
from venture.lite.trace import Trace as LiteTrace

from venture.mite.builtin import builtInSPs
from venture.mite.builtin import builtInValues
from venture.mite.evaluator import evalFamily, unevalFamily, processMadeSP
from venture.mite.evaluator import constrain, unconstrain
from venture.mite.evaluator import restore
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
    processMadeSP(self, spNode)
    self.globalEnv.addBinding(name, spNode)

  ## Internal interface to eval/regen

  def createApplicationNodes(self, address, operatorNode, operandNodes, env):
    # Request nodes don't exist now, so just create a singular node.
    outputNode = OutputNode(address, operatorNode, operandNodes, None, env)
    self.addChildAt(operatorNode, outputNode)
    for operandNode in operandNodes:
      self.addChildAt(operandNode, outputNode)
    return outputNode

  def argsAt(self, node):
    return Args(self, node)

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
    (w, self.families[id]) = evalFamily(
      EvalContext(self), Address(List(id)),
      self.unboxExpression(exp), self.globalEnv)
    # forward evaluation should not produce a weight
    # (is this always true?)
    assert w == 0

  def uneval(self, id):
    assert id in self.families
    w = unevalFamily(EvalContext(self), self.families[id])
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
      weight += constrain(EvalContext(self), node, node.observedValue)
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
      constrain(EvalContext(self), node, node.observedValue)
    self.unpropagatedObservations.clear()

  def unobserve(self, id):
    node = self.families[id]
    if node.isObservation:
      weight = unconstrain(EvalContext(self), node)
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
      return 'default all'
    print 'select', scope, block
    return None

  def just_detach(self, scaffold):
    if scaffold == 'default all':
      from venture.lite.omegadb import OmegaDB
      weight = 0
      rhoDB = OmegaDB()
      for id in reversed(sorted(self.families)):
        node = self.families[id]
        if node.isObservation:
          weight += unconstrain(RestoreContext(self, rhoDB), self.families[id])
        unevalFamily(RestoreContext(self, rhoDB), node)
      return weight, rhoDB
    print 'detach', scaffold
    return 0, None

  def just_regen(self, scaffold):
    if scaffold == 'default all':
      from venture.lite.omegadb import OmegaDB
      weight = 0
      rhoDB = OmegaDB()
      for id in sorted(self.families):
        node = self.families[id]
        restore(EvalContext(self), node)
        if node.isObservation:
          weight += constrain(RestoreContext(self, rhoDB), node, node.observedValue)
      return weight
    print 'regen', scaffold
    return 0

  def just_restore(self, scaffold, rhoDB):
    if scaffold == 'default all':
      weight = 0
      for id in sorted(self.families):
        node = self.families[id]
        restore(RestoreContext(self, rhoDB), node)
        if node.isObservation:
          weight += constrain(RestoreContext(self, rhoDB), node, node.observedValue)
      return weight
    print 'restore', scaffold, rhoDB
    return 0

  ## Serialization interface

  def makeSerializationDB(self, values=None, skipStackDictConversion=False):
    from venture.lite.omegadb import OmegaDB
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
    unevalFamily(RestoreContext(self, db), self.families[id])

  def restore(self, id, db):
    assert id in self.families
    restore(RestoreContext(self, db), self.families[id])

  def evalAndRestore(self, id, exp, db):
    assert id not in self.families
    (w, self.families[id]) = evalFamily(
      RestoreContext(self, db), Address(List(id)),
      self.unboxExpression(exp), self.globalEnv)
    assert w == 0

class EvalContext(object):
  def __init__(self, trace):
    self.trace = trace

  def __getattr__(self, name):
    # proxy the trace interface to eval/regen
    if name in [
        'createConstantNode', 'createLookupNode', 'createApplicationNodes',
        'spAt', 'argsAt', 'valueAt', 'setValueAt',
        'madeSPRecordAt', 'setMadeSPRecordAt',
        'parentsAt', 'childrenAt',
        'disconnectLookup', 'reconnectLookup']:
      return getattr(self.trace, name)
    else:
      return object.__getattribute__(self, name)

  def argsAt(self, node):
    return Args(self.trace, node, context=self)

  def applyCall(self, sp, args):
    return sp.apply(args)

  def unapplyCall(self, sp, args):
    return sp.unapply(args)

  ## Request interface to SPs

  def newRequest(self, requester, raddr, exp, env):
    if hasattr(raddr, 'address'):
      raddr = raddr.address.last
    address = requester.address.request(List((
      self.trace.spRefAt(requester).makerNode.address.last, raddr)))
    # TODO where to put w?
    (w, requested) = evalFamily(self, address, exp, env)
    assert w == 0
    assert not self.trace.containsSPFamilyAt(requester, raddr), \
      "Tried to make new request at existing address."
    self.trace.registerFamilyAt(requester, raddr, requested)
    self.trace.incRequestsAt(requested)
    return raddr

  def incRequest(self, requester, raddr):
    requested = self.trace.spFamilyAt(requester, raddr)
    self.trace.incRequestsAt(requested)
    return raddr

  def decRequest(self, requester, raddr):
    requested = self.trace.spFamilyAt(requester, raddr)
    self.trace.decRequestsAt(requested)
    if self.trace.numRequestsAt(requested) == 0:
      self.trace.unregisterFamilyAt(requester, raddr)
      # TODO where to put w?
      w = unevalFamily(self, requested)
      assert w == 0

  def hasRequest(self, requester, raddr):
    return self.trace.containsSPFamilyAt(requester, raddr)

  def constrainRequest(self, requester, raddr, value):
    requested = self.trace.spFamilyAt(requester, raddr)
    return constrain(self, requested, value, child=requester)

  def unconstrainRequest(self, requester, raddr):
    requested = self.trace.spFamilyAt(requester, raddr)
    return unconstrain(self, requested, child=requester)

  def requestedValue(self, requester, raddr):
    requested = self.trace.spFamilyAt(requester, raddr)
    return self.trace.valueAt(requested)

  def setState(self, _node, _value):
    pass

  def getState(self, _node):
    assert False, "Cannot restore outside a regeneration context"

from collections import Iterable
def normalize(address):
  if isinstance(address, Iterable):
    return tuple(normalize(part) for part in address)
  else:
    return address

class RestoreContext(EvalContext):
  def __init__(self, trace, omegaDB):
    super(RestoreContext, self).__init__(trace)
    self.omegaDB = omegaDB

  def applyCall(self, sp, args):
    return sp.restore(args)

  def setState(self, node, value):
    self.omegaDB.extractValue(normalize(node.address.last), value)

  def getState(self, node):
    return self.omegaDB.getValue(normalize(node.address.last))
