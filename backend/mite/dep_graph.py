from collections import OrderedDict

from venture.lite.value import SPRef

from venture.untraced.node import Node

import venture.mite.address as addresses
from venture.mite.sp import VentureSP
from venture.mite.sp_registry import registerBuiltinSP
from venture.mite.traces import AbstractTrace
from venture.mite.traces import VentureTraceConstructorSP

from venture.mite.evaluator import Regenerator, Restorer


class DependencyNode(object):
  def __init__(self, addr):
    self.address = addr
    self.children = set()

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


class DependencyGraphTrace(AbstractTrace):
  """Maintain a dynamic dependency graph of the program execution.

  This corresponds to the "probabilistic execution trace"
  implementation approach.

  """

  def __init__(self, seed):
    self.requests = {}
    self.results = OrderedDict()
    self.made_sps = {}
    self.nodes = {}
    super(DependencyGraphTrace, self).__init__(seed)

  def register_request(self, addr, exp, env):
    self.requests[addr] = (exp, env)

  def register_constant(self, addr, value):
    self.nodes[addr] = ConstantNode(addr)
    self.results[addr] = value

  def register_lookup(self, addr, node):
    assert node.value is self.results[node.address]
    self.nodes[addr] = LookupNode(addr, node.address)
    self.results[addr] = node.value
    self.add_child_at(node.address, addr)

  def register_application(self, addr, arity, value):
    parents = [addresses.subexpression(index, addr)
               for index in range(arity)]
    self.nodes[addr] = ApplicationNode(addr, parents[0], parents[1:])
    self.results[addr] = value
    for parent_addr in parents:
      self.add_child_at(parent_addr, addr)

  def add_child_at(self, parent_addr, child_addr):
    self.nodes[parent_addr].children.add(child_addr)

  def register_made_sp(self, addr, sp):
    assert self.results[addr] is sp
    self.made_sps[addr] = sp
    self.results[addr] = ret = SPRef(Node(addr, sp))
    return ret

  def deref_sp(self, sp_ref):
    addr = sp_ref.makerNode.address
    sp = self.made_sps[addr]
    return Node(addr, sp)

  def value_at(self, addr):
    return self.results[addr]

  def unregister_made_sp(self, addr):
    sp = self.made_sps[addr]
    del self.made_sps[addr]
    self.results[addr] = sp
    return sp

  def single_site_subproblem(self, address, kernel=None):
    return single_site_scaffold(self, address, kernel)

  def unregister_request(self, addr):
    del self.requests[addr]

  def unregister_constant(self, addr):
    del self.results[addr]
    del self.nodes[addr]

  def unregister_lookup(self, addr):
    node = self.nodes[addr]
    self.remove_child_at(node.orig_addr, addr)
    del self.results[addr]
    del self.nodes[addr]

  def unregister_application(self, addr):
    node = self.nodes[addr]
    for parent_addr in node.parents():
      self.remove_child_at(parent_addr, addr)
    del self.nodes[addr]
    del self.results[addr]

  def remove_child_at(self, parent_addr, child_addr):
    self.nodes[parent_addr].children.remove(child_addr)

  def unregister_made_sp(self, addr):
    sp = self.made_sps[addr]
    del self.made_sps[addr]
    self.results[addr] = sp
    return sp

  def extract(self, subproblem):
    x = DependencyGraphRegenerator(self, subproblem)
    weight = x.extract_subproblem()
    return (weight, x.fragment)

  def regen(self, subproblem, trace_fragment):
    x = DependencyGraphRegenerator(self, subproblem, trace_fragment)
    weight = x.regen_subproblem()
    return weight

  def restore(self, subproblem, trace_fragment):
    x = DependencyGraphRestorer(self, subproblem, trace_fragment)
    x.regen_subproblem()


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
    weight = 0

    node = self.trace.nodes[addr]
    if isinstance(node, LookupNode):
      del self.trace.results[addr]
    else:
      # unapply
      assert isinstance(node, ApplicationNode)
      value = self.trace.value_at(addr)
      if isinstance(value, SPRef) and value.makerNode is addr:
        value = self.trace.unregister_made_sp(addr)
      del self.trace.results[addr]

      sp_node = self.trace.deref_sp(
        self.trace.value_at(node.operator_addr))

      args = []
      for subaddr in node.operand_addrs:
        args.append(Node(subaddr, self.trace.value_at(subaddr)))

      weight += self.unapply_sp(addr, value, sp_node, args)

    return weight

  def regen(self, addr):
    weight = 0

    node = self.trace.nodes[addr]
    if isinstance(node, LookupNode):
      self.trace.results[addr] = self.trace.value_at(node.orig_addr)
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

      self.trace.results[addr] = value
      if isinstance(value, VentureSP):
        _value = self.trace.register_made_sp(addr, value)

    return weight


class DependencyGraphRestorer(DependencyGraphRegenerator, Restorer):
  pass


def single_site_scaffold(trace, principal_address, principal_kernel=None):
  # dependency aware implementation to find a single-site scaffold.
  # somewhat brittle.

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
    if parent is not None:
      regen_parents.setdefault(addr, set()).add(parent)
    if addr in drg:
      continue

    node = trace.nodes[addr]
    propagate = False

    if isinstance(node, LookupNode):
      assert node.orig_addr == parent
      kernels[addr] = {'type': 'propagate_lookup'}
      propagate = True
    else:
      # SP application
      assert isinstance(node, ApplicationNode)
      if addr == principal_address:
        kernels[addr] = principal_kernel
        propagate = True
      if node.operator_addr in drg:
        # operator changed
        kernels[addr] = {'type': 'proposal'}
        propagate = True
      elif any(operand in drg for operand in node.operand_addrs):
        # operands changed
        sp_ref = trace.value_at(node.operator_addr)
        sp = trace.deref_sp(sp_ref).value
        val = trace.value_at(addr)
        kernel = sp.constraint_kernel(None, addr, val)
        if kernel is NotImplemented or likelihood_free_lite_sp(sp):
          kernels[addr] = {'type': 'proposal'}
          propagate = True
        else:
          kernels[addr] = {'type': 'constraint', 'val': val}
      elif isinstance(parent, addresses.request) and addr == parent.request_id:
        kernels[addr] = {'type': 'propagate_request', 'parent': parent}
        propagate = True

    if propagate:
      drg.add(addr)
      request_children = []
      if isinstance(addr, addresses.request):
        # XXX STUB: hack in dependencies due to requests of compound SPs
        if isinstance(addr.request_id, addresses.Address):
          request_children = [addr.request_id]
      for child in list(node.children) + request_children:
        q.append((child, addr))

  from venture.mite.scaffold import Scaffold
  from collections import OrderedDict
  # XXX remove dependency on toposort
  import toposort
  assert set(kernels) == set(regen_parents)
  kernels = OrderedDict([
    (addr, kernels[addr])
    for addr in toposort.toposort_flatten(regen_parents)
  ])
  return Scaffold(kernels)
