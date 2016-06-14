import numbers
from contextlib import contextmanager

from venture.exception import VentureException
from venture.lite.address import List
from venture.lite.node import isConstantNode
from venture.lite.node import isLookupNode
from venture.lite.node import isOutputNode
from venture.lite.value import SPRef
import venture.lite.exp as e

from venture.untraced.node import Node, normalize

import venture.mite.address as addresses
from venture.mite.sp import VentureSP
from venture.mite.sps.compound import CompoundSP

class Evaluator(object):
  """Core of the evaluator."""

  def __init__(self, trace):
    self.trace = trace

  def eval_family(self, addr, exp, env):
    weight = 0
    value = None

    if e.isVariable(exp):
      result_node = env.findSymbol(exp)
      self.trace.register_lookup(addr, result_node.address)
      value = result_node.value
    elif e.isSelfEvaluating(exp):
      value = normalize(exp)
      self.trace.register_constant(addr, value)
    elif e.isQuotation(exp):
      value = normalize(e.textOfQuotation(exp))
      self.trace.register_constant(addr, value)
    elif e.isLambda(exp):
      (params, body) = e.destructLambda(exp)
      sp = CompoundSP(params, body, env)
      self.trace.register_constant(addr, sp)
      value = self.trace.register_made_sp(addr, sp)
    else:
      # SP application
      nodes = []
      for index, subexp in enumerate(exp):
        subaddr = addresses.subexpression(index, addr)
        w, v = self.eval_family(subaddr, subexp, env)
        weight += w
        nodes.append(Node(subaddr, v))

      sp_node = self.trace.deref_sp(nodes[0])
      args = nodes[1:]

      handle = self.construct_trace_handle(addr, sp_node.address, args)
      w, value = self.apply_sp(sp_node.value, handle)
      weight += w

      self.trace.register_application(addr, len(exp), value)
      if isinstance(value, VentureSP):
        value = self.trace.register_made_sp(addr, value)

    return (weight, value)

  def construct_trace_handle(self, app_addr, sp_addr, args):
    return TraceHandle(self.trace, app_addr, sp_addr, args)

  def apply_sp(self, sp, args):
    return (0, sp.apply(args))

# TODO: this signature retains backward compatibility with Args for now,
# but we should remove that
from venture.lite.psp import IArgs
class TraceHandle(IArgs):
  def __init__(self, trace, app_addr, sp_addr, args):
    self.trace = trace
    self.node = app_addr
    self.sp_addr = sp_addr
    self.operandNodes = args
    self.env = None

  def operandValues(self):
    return [node.value for node in self.operandNodes]

  def py_prng(self):
    return self.trace.py_prng

  def np_prng(self):
    return self.trace.np_prng

  def request_address(self, request_id):
    return addresses.request(self.sp_addr, request_id)

  def newRequest(self, request_id, exp, env):
    # TODO return Node(value, address) so that SPs don't have to use
    # requestedValue all the time; this way the untraced interpreter
    # doesn't have to retain requests with non-repeatable request_ids.
    addr = self.request_address(request_id)
    w, _ = self.trace.eval_request(addr, exp, env)
    assert w == 0
    return request_id

  def incRequest(self, request_id):
    # TODO remove ref-counting from trace layer
    return request_id

  def hasRequest(self, request_id):
    # TODO remove ref-counting from trace layer
    # XXX for now, this breaks the trace abstraction
    addr = self.request_address(request_id)
    return addr in self.trace.results

  def requestedValue(self, request_id):
    addr = self.request_address(request_id)
    return self.trace.value_at(addr)

@contextmanager
def annotation(address):
  try:
    yield
  except VentureException:
    raise # Avoid rewrapping with the below
  except Exception as err:
    import sys
    info = sys.exc_info()
    raise VentureException("evaluation", err.message, address=address,
                           cause=err), None, info[2]

class EvalContext(object):
  def __init__(self, trace):
    self.trace = trace

  ## override these methods to control behavior at application nodes

  def applyCall(self, sp, args):
    return sp.apply(args)

  def unapplyCall(self, sp, args):
    return sp.unapply(args)

  def constrainCall(self, sp, value, args):
    return sp.constrain(value, args)

  def unconstrainCall(self, sp, args):
    return sp.unconstrain(args)

  ## evaluation

  def evalFamily(self, address, exp, env):
    weight = 0
    if e.isVariable(exp):
      with annotation(address):
        sourceNode = env.findSymbol(exp)
      # weight = regen(trace, sourceNode, scaffold,
      #                shouldRestore, omegaDB, gradients)
      return (weight, self.trace.createLookupNode(address, sourceNode))
    elif e.isSelfEvaluating(exp):
      return (0, self.trace.createConstantNode(address, exp))
    elif e.isQuotation(exp):
      return (0, self.trace.createConstantNode(address, e.textOfQuotation(exp)))
    elif e.isLambda(exp):
      (params, body) = e.destructLambda(exp)
      sp = CompoundSP(params, body, env)
      spNode = self.trace.createConstantNode(address, sp)
      self.processMadeSP(spNode)
      return (0, spNode)
    else:
      weight = 0
      nodes = []
      for index, subexp in enumerate(exp):
        addr = address.extend(index)
        w, n = self.evalFamily(addr, subexp, env)
        weight += w
        nodes.append(n)
      outputNode = self.trace.createApplicationNodes(address, nodes[0], nodes[1:], env)
      with annotation(address):
        weight += self.apply(outputNode)
      assert isinstance(weight, numbers.Number)
      return weight, outputNode

  def apply(self, node):
    sp = self.trace.spAt(node)
    args = self.trace.argsAt(node, context=self)
    assert isinstance(sp, VentureSP)

    # if omegaDB.hasValueFor(node): oldValue = omegaDB.getValue(node)
    # else: oldValue = None

    weight = 0
    # if scaffold.hasLKernel(node):
    # else:
    newValue = self.applyCall(sp, args)

    self.trace.setValueAt(node, newValue)
    if isinstance(newValue, VentureSP):
      self.processMadeSP(node)
    # if sp.isRandom(): trace.registerRandomChoice(node)
    # if isTagOutputPSP(psp):
    assert isinstance(weight, numbers.Number)
    return weight

  def processMadeSP(self, node):
    sp = self.trace.valueAt(node)
    assert isinstance(sp, VentureSP)
    # if isAAA:
    #   trace.discardAAAMadeSPAuxAt(node)
    # if sp.hasAEKernel(): trace.registerAEKernel(node)
    self.trace.setMadeSPRecordAt(node, sp)
    self.trace.setValueAt(node, SPRef(node))

  def constrain(self, node, value, child=None):
    if self.trace.childrenAt(node) - set([child]):
      raise VentureException("evaluation", "Cannot constrain " \
        "a value that is referenced more than once.", address=node.address)
    if isConstantNode(node):
      raise VentureException("evaluation", "Cannot constrain " \
        "a constant value.", address=node.address)
    elif isLookupNode(node):
      weight = self.constrain(node.sourceNode, value, child=node)
      self.trace.setValueAt(node, value)
      return weight
    else:
      assert isOutputNode(node)
      sp = self.trace.spAt(node)
      args = self.trace.argsAt(node, context=self)
      with annotation(node.address):
        weight = self.constrainCall(sp, value, args)
      self.trace.setValueAt(node, value)
      # trace.registerConstrainedChoice(node)
      assert isinstance(weight, numbers.Number)
      return weight

  ## unevaluation

  def unevalFamily(self, node):
    weight = 0
    if isConstantNode(node): pass
    elif isLookupNode(node):
      assert len(self.trace.parentsAt(node)) == 1
      self.trace.disconnectLookup(node)
      self.trace.setValueAt(node, None)
      # weight += extractParents(trace, node, scaffold, omegaDB, compute_gradient)
    else:
      assert isOutputNode(node)
      weight += self.unapply(node)
      for operandNode in reversed(node.operandNodes):
        weight += self.unevalFamily(operandNode)
      weight += self.unevalFamily(node.operatorNode)
    return weight

  def unapply(self, node):
    sp = self.trace.spAt(node)
    args = self.trace.argsAt(node, context=self)
    # if isTagOutputPSP(psp):
    # if sp.isRandom(): trace.registerRandomChoice(node)
    value = self.trace.valueAt(node)
    if (isinstance(value, SPRef) and value.makerNode is node):
      self.teardownMadeSP(node)

    weight = 0
    # if scaffold.hasLKernel(node):
    # else:
    self.unapplyCall(sp, args)

    self.trace.setValueAt(node, None)
    # if compute_gradient:
    return weight

  def teardownMadeSP(self, node):
    sp = self.trace.madeSPRecordAt(node)
    assert isinstance(sp, VentureSP)
    # assert len(spRecord.spFamilies.families) == 0
    self.trace.setValueAt(node, sp)
    # if sp.hasAEKernel(): trace.unregisterAEKernel(node)
    # if isAAA:
    #   trace.registerAAAMadeSPAuxAt(node,trace.madeSPAuxAt(node))
    self.trace.setMadeSPRecordAt(node, None)

  def unconstrain(self, node, child=None):
    if self.trace.childrenAt(node) - set([child]):
      raise VentureException("evaluation", "Cannot unconstrain " \
        "a value that is referenced more than once.", address=node.address)
    if isLookupNode(node):
      weight = self.unconstrain(node.sourceNode, child=node)
      self.trace.setValueAt(node, self.trace.valueAt(node.sourceNode))
      return weight
    else:
      assert isOutputNode(node)
      sp = self.trace.spAt(node)
      args = self.trace.argsAt(node, context=self)
      with annotation(node.address):
        weight, value = self.unconstrainCall(sp, args)
      self.trace.setValueAt(node, value)
      # trace.unregisterConstrainedChoice(node)
      assert isinstance(weight, numbers.Number)
      return weight

  ## restoration

  def restore(self, node):
    weight = 0
    if isConstantNode(node): return 0
    if isLookupNode(node):
      # weight = regenParents(trace, node, scaffold, True, omegaDB, gradients)
      self.trace.reconnectLookup(node)
      self.trace.setValueAt(node, self.trace.valueAt(node.sourceNode))
      assert isinstance(weight, numbers.Number)
      return weight
    else: # node is output node
      assert isOutputNode(node)
      weight = self.restore(node.operatorNode)
      for operandNode in node.operandNodes:
        weight += self.restore(operandNode)
      weight += self.apply(node)
      assert isinstance(weight, numbers.Number)
      return weight

  ## request interface to SPs

  def newRequest(self, requester, raddr, exp, env):
    base = self.trace.spRefAt(requester).makerNode.address.last
    ext = raddr
    if hasattr(ext, 'address'):
      ext = raddr.address.last
    address = requester.address.request(List((base, ext)))
    # TODO where to put w?
    (w, requested) = self.evalFamily(address, exp, env)
    assert w == 0
    if self.trace.containsSPFamilyAt(requester, raddr):
      raise VentureException("evaluation",
        "Tried to make new request at existing address.",
        address=requester.address)
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
      w = self.unevalFamily(requested)
      assert w == 0

  def hasRequest(self, requester, raddr):
    return self.trace.containsSPFamilyAt(requester, raddr)

  def constrainRequest(self, requester, raddr, value):
    requested = self.trace.spFamilyAt(requester, raddr)
    return self.constrain(requested, value, child=requester)

  def unconstrainRequest(self, requester, raddr):
    requested = self.trace.spFamilyAt(requester, raddr)
    return self.unconstrain(requested, child=requester)

  def requestedValue(self, requester, raddr):
    requested = self.trace.spFamilyAt(requester, raddr)
    return self.trace.valueAt(requested)

  def setState(self, node, value, ext=None):
    pass

  def getState(self, node, ext=None):
    raise VentureException("evaluation",
      "Cannot restore outside a regeneration context",
      address=node.address)

from collections import Iterable
def asFrozenList(address):
  if isinstance(address, Iterable) and not isinstance(address, basestring):
    return tuple(asFrozenList(part) for part in address)
  else:
    return address

class RestoreContext(EvalContext):
  def __init__(self, trace, omegaDB):
    super(RestoreContext, self).__init__(trace)
    self.omegaDB = omegaDB

  def applyCall(self, sp, args):
    return sp.restore(args)

  def constrainCall(self, sp, value, args):
    return sp.reconstrain(value, args)

  def setState(self, node, value, ext=None):
    address = node.address.last
    if ext is not None:
      address = (address, ext)
    self.omegaDB.extractValue(asFrozenList(address), value)

  def getState(self, node, ext=None):
    address = node.address.last
    if ext is not None:
      address = (address, ext)
    return self.omegaDB.getValue(asFrozenList(address))
