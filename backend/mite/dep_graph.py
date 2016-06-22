import venture.lite.types as t
from venture.lite.value import SPRef

from venture.untraced.node import Node

import venture.mite.address as addresses
from venture.mite.sp import SimulationSP
from venture.mite.sp_registry import registerBuiltinSP
from venture.mite.traces import AbstractTrace


class GraphTraceSP(SimulationSP):
  def simulate(self, args):
    seed = args.py_prng().randint(1, 2**31 - 1)
    return t.Blob.asVentureValue(DependencyGraphTrace(seed))

registerBuiltinSP("graph_trace", GraphTraceSP())


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
    self.results = {}
    self.made_sps = {}
    self.nodes = {}
    self.children = {}
    self.observations = {}
    super(DependencyGraphTrace, self).__init__(seed)

  def register_request(self, addr, exp, env):
    self.requests[addr] = (exp, env)

  def register_response(self, addr, value):
    assert self.results[addr] is value

  def register_constant(self, addr, value):
    self.nodes[addr] = ConstantNode(addr)
    self.results[addr] = value

  def register_lookup(self, addr, orig_addr):
    self.nodes[addr] = LookupNode(addr, orig_addr)
    self.results[addr] = self.results[orig_addr]
    self.add_child_at(orig_addr, addr)

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
    self.results[addr] = ret = SPRef(addr)
    return ret

  def deref_sp(self, sp_ref):
    addr = sp_ref.makerNode
    sp = self.made_sps[addr]
    return Node(addr, sp)

  def register_observation(self, addr, value):
    self.observations[addr] = value

  def value_at(self, addr):
    return self.results[addr]

  def check_consistent(self):
    return all(self.results[id] == self.observations[id]
               for id in self.observations)
