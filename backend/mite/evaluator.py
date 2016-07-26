from collections import namedtuple

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
      # XXX hack to propagate regenerated global bindings
      try:
        result_node.value = self.trace.value_at(result_node.address)
      except KeyError:
        pass
      self.trace.register_lookup(addr, result_node)
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

      sp_node = self.trace.deref_sp(nodes[0].value)
      args = nodes[1:]

      w, value = self.apply_sp(addr, sp_node, args)
      weight += w

      self.trace.register_application(addr, len(exp), value)
      if isinstance(value, VentureSP):
        value = self.trace.register_made_sp(addr, value)

    return (weight, value)

  def apply_sp(self, addr, sp_node, args):
    sp = sp_node.value
    handle = TraceHandle(self.trace, sp_node.address)
    return (0, sp.apply(handle, addr, args))

class TraceHandle(object):
  def __init__(self, trace, sp_addr):
    self.trace = trace
    self.node = None
    self.sp_addr = sp_addr
    self.env = None

  def py_prng(self):
    return self.trace.py_prng

  def np_prng(self):
    return self.trace.np_prng

  PRNG = namedtuple('TracePRNG', ['py_prng', 'np_prng'])

  def prng(self):
    return self.PRNG(self.trace.py_prng, self.trace.np_prng)

  def request_address(self, request_id):
    return addresses.request(self.sp_addr, request_id)

  def new_request(self, request_id, exp, env):
    # TODO return Node(value, address) so that SPs don't have to use
    # requestedValue all the time; this way the untraced interpreter
    # doesn't have to retain requests with non-repeatable request_ids.
    addr = self.request_address(request_id)
    w, _ = self.trace.eval_request(addr, exp, env)
    assert w == 0
    return request_id

  def value_at(self, request_id):
    # TODO have this accept a Node(value, address),
    # as returned by new_request
    addr = self.request_address(request_id)
    return self.trace.value_at(addr)


class Regenerator(Evaluator):
  """Unevaluate and regenerate according to a scaffold."""

  def __init__(self, trace, scaffold, fragment=None):
    self.trace = trace
    self.scaffold = scaffold
    if fragment is None:
      fragment = {} # addr -> result value
    self.fragment = fragment

  def uneval_family(self, addr, exp, env):
    weight = 0

    if e.isVariable(exp):
      self.trace.unregister_lookup(addr)
    elif e.isSelfEvaluating(exp) or e.isQuotation(exp) or e.isLambda(exp):
      self.trace.unregister_constant(addr)
    else:
      # unapply
      value = self.trace.value_at(addr)
      if isinstance(value, SPRef) and value.makerNode is addr:
        value = self.trace.unregister_made_sp(addr)
      self.trace.unregister_application(addr)

      nodes = []
      for index, subexp in enumerate(exp):
        subaddr = addresses.subexpression(index, addr)
        nodes.append(Node(subaddr, self.trace.value_at(subaddr)))

      sp_node = self.trace.deref_sp(nodes[0].value)
      args = nodes[1:]

      weight += self.unapply_sp(addr, value, sp_node, args)

      # uneval operands
      for node, subexp in reversed(zip(nodes, exp)):
        weight += self.uneval_family(node.address, subexp, env)

    return weight

  def unapply_sp(self, addr, value, sp_node, args):
    sp = sp_node.value
    handle = RegeneratingTraceHandle(
      self.trace, sp_node.address, self)

    kernel = self.scaffold.kernel_at(sp, handle, addr)
    if kernel is None:
      kernel = sp.proposal_kernel(handle, addr)

    (weight, fragment) = kernel.extract(value, args)
    self.fragment[addr] = (fragment, sp, args)
    return weight

  def apply_sp(self, addr, sp_node, args):
    sp = sp_node.value
    handle = RegeneratingTraceHandle(
      self.trace, sp_node.address, self)

    kernel = self.scaffold.kernel_at(sp, handle, addr)
    if kernel is None:
      kernel = sp.proposal_kernel(handle, addr)
      fragment = self.fragment_to_maybe_restore(addr, sp, args)
    else:
      fragment = None

    if fragment is not None:
      return (0, kernel.restore(args, fragment["value"]))
    else:
      return kernel.regen(args)

  def fragment_to_maybe_restore(self, addr, sp, args):
    if addr not in self.fragment:
      # nothing to restore
      return None
    else:
      (fragment, old_sp, old_args) = self.fragment[addr]
      # check if the parents have changed
      if old_sp is not sp:
        if not (isinstance(sp, CompoundSP) and
                isinstance(old_sp, CompoundSP) and
                sp.params == old_sp.params and
                sp.exp == old_sp.exp and
                sp.env is old_sp.env):
          return None
      for (arg, old_arg) in zip(args, old_args):
        if not self.is_same_arg(arg, old_arg):
          return None
      # wrap it in a dict to distinguish from None
      return {"value": fragment}

  def is_same_arg(self, arg, old_arg):
    if (isinstance(arg.value, SPRef) and
        isinstance(old_arg.value, SPRef)):
      arg_sp = self.trace.deref_sp(arg.value)
      old_arg_sp = self.trace.deref_sp(old_arg.value)
      return arg_sp.value is old_arg_sp.value
    else:
      return arg.value == old_arg.value


class Restorer(Regenerator):
  """Restore from the trace fragment produced by uneval."""

  def apply_sp(self, addr, sp_node, args):
    sp = sp_node.value
    handle = RegeneratingTraceHandle(
      self.trace, sp_node.address, self)

    kernel = self.scaffold.kernel_at(sp, handle, addr)
    if kernel is None:
      kernel = sp.proposal_kernel(handle, addr)

    fragment = self.fragment_to_maybe_restore(addr, sp, args)
    assert fragment is not None
    return (0, kernel.restore(args, fragment["value"]))


class RegeneratingTraceHandle(TraceHandle):
  def __init__(self, trace, sp_addr, regenerator):
    super(RegeneratingTraceHandle, self).__init__(
      trace, sp_addr)
    self.regenerator = regenerator

  def free_request(self, request_id):
    addr = self.request_address(request_id)
    (exp, env) = self.trace.requests[addr]
    w = self.regenerator.uneval_family(addr, exp, env)
    assert w == 0
    return request_id

  def restore_request(self, request_id):
    addr = self.request_address(request_id)
    (exp, env) = self.trace.requests[addr]
    w, _ = self.regenerator.eval_family(addr, exp, env)
    assert w == 0
    return request_id
