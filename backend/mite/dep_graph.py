import os
import sys

from venture.lite.value import SPRef

from venture.untraced.node import Node

import venture.mite.address as addresses
from venture.mite.sp import VentureSP
from venture.mite.sp_registry import registerBuiltinSP
from venture.mite.traces import AbstractCompleteTrace
from venture.mite.traces import AbstractTrace
from venture.mite.traces import ResultTrace
from venture.mite.traces import SourceTracing
from venture.mite.traces import VentureTraceConstructorSP
from venture.mite.util import log_regen_event
from venture.mite.util import log_regen_event_at
from venture.mite.util import log_scaffold_event
from venture.mite.util import log_scaffold_event_at

from venture.mite.evaluator import Regenerator, Restorer

class DependencyNode(object):
  def __init__(self, addr):
    self.address = addr
    self.children = set()
    self.application_children = set() # the set of applications whose operator is this node

  def parents(self):
    raise NotImplementedError("Cannot get the parents of an abstract node.")


class ConstantNode(DependencyNode):
  def __init__(self, addr):
    super(ConstantNode, self).__init__(addr)

  def parents(self): return []


class LookupNode(DependencyNode):
  def __init__(self, addr, orig_addr):
    super(LookupNode, self).__init__(addr)
    self.orig_addr = orig_addr

  def parents(self): return [self.orig_addr]


class ApplicationNode(DependencyNode):
  def __init__(self, addr, operator_addr, operand_addrs):
    super(ApplicationNode, self).__init__(addr)
    self.operator_addr = operator_addr
    self.operand_addrs = operand_addrs

  def parents(self): return [self.operator_addr] + self.operand_addrs


class DependencyGraphTrace(SourceTracing, AbstractCompleteTrace, ResultTrace, AbstractTrace):
  """Maintain a dynamic dependency graph of the program execution.

  This corresponds to the "probabilistic execution trace"
  implementation approach.

  """

  def __init__(self, seed):
    self.nodes = {}
    super(DependencyGraphTrace, self).__init__(seed)

  def checkInvariants(self):
    ans = self.violatedInvariants()
    if len(ans) > 0:
      print >>sys.stderr, "Invariant violation detected"
      for (msg, addr) in ans:
        print >>sys.stderr, msg
        self.print_stack(addr, stream=sys.stderr)
    assert len(ans) == 0, ans

  def violatedInvariants(self):
    ans = []
    touched = set()
    def touch(addr):
      if addr not in touched:
        ans.extend(self.violatedInvariantsAt(addr))
        touched.add(addr)
    for (addr, node) in self.nodes.iteritems():
      touch(addr)
      for addr in node.children:
        touch(addr)
      for addr in node.application_children:
        touch(addr)
    for (addr, _) in self.results.iteritems():
      touch(addr)
    for (addr, _) in self.requests.iteritems():
      touch(addr)
    return ans

  def violatedInvariantsAt(self, addr):
    ans = []
    if addr not in self.nodes:
      ans.append(("No node at", addr))
    if not self.has_value_at(addr):
      ans.append(("No value at", addr))
    if isinstance(addr, addresses.RequestAddress) and addr not in self.requests:
      ans.append(("No request registered at", addr))
    return ans

  def register_constant(self, addr, value):
    self.nodes[addr] = ConstantNode(addr)
    self.record_result(addr, value)

  def register_lookup(self, addr, node):
    assert node.value is self.results[node.address]
    self.nodes[addr] = LookupNode(addr, node.address)
    self.record_result(addr, node.value)
    self.add_child_at(node.address, addr)

  def register_application(self, addr, arity, value):
    parents = [addresses.subexpression(index, addr)
               for index in range(arity)]
    operator = parents[0]
    operands = parents[1:]
    self.nodes[addr] = ApplicationNode(addr, operator, operands)
    self.record_result(addr, value)
    self.add_application_child_at(operator, addr)
    for operand in operands:
      self.add_child_at(operand, addr)

  def add_child_at(self, parent_addr, child_addr):
    self.nodes[parent_addr].children.add(child_addr)

  def add_application_child_at(self, parent_addr, child_addr):
    self.nodes[parent_addr].children.add(child_addr)
    sp_node = self.deref_sp(self.value_at(parent_addr))
    self.nodes[sp_node.address].application_children.add(child_addr)

  ## support for regen/extract

  def single_site_subproblem(self, address, kernel=None):
    return single_site_scaffold(self, address, kernel)

  def unregister_constant(self, addr):
    self.forget_result(addr)
    del self.nodes[addr]

  def unregister_lookup(self, addr):
    node = self.nodes[addr]
    self.remove_child_at(node.orig_addr, addr)
    self.forget_result(addr)
    del self.nodes[addr]

  def unregister_application(self, addr):
    node = self.nodes[addr]
    self.remove_application_child_at(node.operator_addr, addr)
    for operand in node.operand_addrs:
      self.remove_child_at(operand, addr)
    del self.nodes[addr]
    self.forget_result(addr)

  def remove_child_at(self, parent_addr, child_addr):
    self.nodes[parent_addr].children.remove(child_addr)

  def remove_application_child_at(self, parent_addr, child_addr):
    self.nodes[parent_addr].children.remove(child_addr)
    sp_node = self.deref_sp(self.value_at(parent_addr))
    self.nodes[sp_node.address].application_children.remove(child_addr)

  def extract(self, subproblem):
    log_regen_event("Dependency-extracting", subproblem)
    x = DependencyGraphRegenerator(self, subproblem)
    weight = x.extract_subproblem()
    log_regen_event("Done dependency-extracting", subproblem)
    return (weight, x.fragment)

  def regen(self, subproblem, trace_fragment):
    log_regen_event("Dep regenerating", subproblem)
    x = DependencyGraphRegenerator(self, subproblem, trace_fragment)
    weight = x.regen_subproblem()
    log_regen_event("Done dep regenerating", subproblem)
    return weight

  def restore(self, subproblem, trace_fragment):
    log_regen_event("Dep restoring", subproblem)
    x = DependencyGraphRestorer(self, subproblem, trace_fragment)
    x.regen_subproblem()
    log_regen_event("Done dep restoring", subproblem)


registerBuiltinSP("graph_trace", VentureTraceConstructorSP(
  DependencyGraphTrace))


class DependencyGraphRegenerator(Regenerator):
  def extract_subproblem(self):
    weight = 0
    for addr in reversed(self.scaffold.kernels):
      weight += self.extract(addr)
    return weight

  def regen_subproblem(self):
    weight = 0
    for addr in self.scaffold.kernels:
      weight += self.regen(addr)
    return weight

  def extract(self, addr):
    log_regen_event_at("Dependency graph regenerator extracting node", self.trace, addr)
    weight = 0

    node = self.trace.nodes[addr]
    if isinstance(node, LookupNode):
      self.trace.forget_result(addr)
    else:
      # unapply
      assert isinstance(node, ApplicationNode)
      value = self.trace.value_at(addr)
      if isinstance(value, SPRef) and value.makerNode is addr:
        value = self.trace.unregister_made_sp(addr)
      self.trace.forget_result(addr)

      sp_node = self.trace.deref_sp(
        self.trace.value_at(node.operator_addr))

      args = []
      for subaddr in node.operand_addrs:
        args.append(Node(subaddr, self.trace.value_at(subaddr)))

      weight += self.unapply_sp(addr, value, sp_node, args)

    return weight

  def regen(self, addr):
    log_regen_event_at("Dependency graph regenerator regenerating node", self.trace, addr)
    weight = 0

    node = self.trace.nodes[addr]
    if isinstance(node, LookupNode):
      self.trace.record_result(addr, self.trace.value_at(node.orig_addr))
    else:
      # SP application
      assert isinstance(node, ApplicationNode)
      sp_node = self.trace.deref_sp(
        self.trace.value_at(node.operator_addr))

      args = []
      for subaddr in node.operand_addrs:
        args.append(Node(subaddr, self.trace.value_at(subaddr)))

      w, value = self.apply_sp(addr, sp_node, args)
      weight += w

      self.trace.record_result(addr, value)
      if isinstance(value, VentureSP):
        _value = self.trace.register_made_sp(addr, value)

    return weight


class DependencyGraphRestorer(DependencyGraphRegenerator, Restorer):
  pass


def single_site_scaffold(trace, principal_address, principal_kernel=None):
  trace.checkInvariants()
  # dependency aware implementation to find a single-site scaffold.
  # somewhat brittle.
  def log(msg, address):
    log_scaffold_event_at(msg, trace, address)

  # If the input involved calls to `toplevel`, need to inject the ID
  # of the current trace.  Harmless otherwise.
  principal_address = addresses.interpret_address_in_trace(principal_address, trace.trace_id, None)
  log("Building scaffold", principal_address)

  assert isinstance(trace, DependencyGraphTrace)

  q = [(principal_address, None)]
  drg = set()
  kernels = {}
  regen_parents = {principal_address: set()}

  if principal_kernel is None:
    principal_kernel = {'type': 'proposal'}

  def likelihood_free_lite_sp(sp):
    from venture.mite.sps.lite_sp import LiteSP
    if isinstance(sp, LiteSP):
      return not sp.wrapped_sp.outputPSP.canAbsorb(None, None, None)
    else:
      return False

  while q:
    addr, parent = q.pop()

    try:
      node = trace.nodes[addr]
    except KeyError:
      print "Couldn't look up", addr, "in", trace.trace_id
      raise
    kernel = None
    propagate = False

    log("Processing", addr)
    if isinstance(node, LookupNode):
      assert node.orig_addr == parent
      log_scaffold_event("Allocating proagate lookup kernel")
      kernel = {'type': 'propagate_lookup'}
      propagate = True
    else:
      # SP application
      assert isinstance(node, ApplicationNode)
      if addr == principal_address and parent is None:
        # Why check that parent is None?  Because if the
        # principal_address is an application of an SP, and some
        # requests of that SP enter the drg, the principal_address may
        # appear in the queue again.  If that happens, the SP in
        # question should have the opportunity not to repropagate, if
        # the result at the principal node actually doesn't depend on
        # the request in question (which presumably it does not).
        # This scenario can occur if the principal address is an
        # application of a recursive compound SP.
        log_scaffold_event("Allocating principal kernel", principal_kernel)
        kernel = principal_kernel
        propagate = True
      elif node.operator_addr in drg:
        # operator changed
        log_scaffold_event("Allocating proposal kernel b/c operator changed")
        kernel = {'type': 'proposal'}
        propagate = True
      elif any(operand in drg for operand in node.operand_addrs):
        # operands changed
        sp_ref = trace.value_at(node.operator_addr)
        sp = trace.deref_sp(sp_ref).value
        val = trace.value_at(addr)
        kernel = sp.constraint_kernel(None, addr, val)
        if kernel is not NotImplemented and not likelihood_free_lite_sp(sp):
          log_scaffold_event("Allocating constraint kernel")
          kernel = {'type': 'constraint', 'val': val}
        else:
          log_scaffold_event("Allocating proposal kernel b/c cannot constrain")
          kernel = {'type': 'proposal'}
          propagate = True
      elif isinstance(parent, addresses.RequestAddress):
        sp_ref = trace.value_at(node.operator_addr)
        sp_node = trace.deref_sp(sp_ref)
        sp = sp_node.value
        from venture.mite.evaluator import TraceHandle
        handle = TraceHandle(trace, sp_node.address)
        kernel = sp.propagating_kernel(handle, addr, parent)
        if kernel is not None:
          log_scaffold_event("Allocating propagate request kernel")
          kernel = {'type': 'propagate_request', 'parent': parent}
          propagate = True
        else:
          log_scaffold_event("Not allocating request propagation kernel because can't")
      else:
        log_scaffold_event("Not allocating any kernel because no circumstances matched")

    if kernel is not None:
      if addr in kernels:
        if kernel != kernels[addr]:
          assert False, "Trying to overwrite %s with %s; see Issue #646" % (kernels[addr], kernel)
      kernels[addr] = kernel
      if parent is not None:
        # print "Registering dependency of", addr, "on", parent
        regen_parents.setdefault(addr, set()).add(parent)

    if propagate and addr not in drg:
      drg.add(addr)
      request_children = set()
      if isinstance(addr, addresses.RequestAddress):
        # by default, notify all applications of this SP.
        sp_node = trace.nodes[addr.sp_addr]
        request_children = sp_node.application_children
      log_scaffold_event('node %r children %r' % (node, node.children))
      for child in node.children | request_children:
        q.append((child, addr))

  from venture.mite.scaffold import Scaffold
  from collections import OrderedDict
  # XXX remove dependency on toposort
  import toposort
  assert set(kernels) == set(regen_parents)
  try:
    toposorted = toposort.toposort_flatten(regen_parents)
  except ValueError:
    print "Failure when trying to build a scaffold at"
    trace.print_stack(principal_address)
    print "Cyclic dependencies among"
    for a in regen_parents.keys():
      print a
      trace.print_stack(a)
    raise
  kernels = OrderedDict([(addr, kernels[addr]) for addr in toposorted])
  return Scaffold(kernels)
