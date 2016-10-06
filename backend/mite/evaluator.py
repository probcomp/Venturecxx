from collections import namedtuple

from venture.lite.value import SPRef
from venture.untraced.node import Node, normalize
import venture.lite.exp as e

from venture.mite.sp import VentureSP
from venture.mite.sps.compound import CompoundSP
import venture.mite.address as addresses

class Evaluator(object):
  """Core of the evaluator."""

  def __init__(self, trace):
    self.trace = trace

  def eval_request(self, addr, exp, env):
    self.trace.register_request(addr, exp, env)
    return self.eval_family(addr, exp, env)

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
      if isinstance(value, SPRef):
        # HACK in case it's a toplevel compound SP definition spliced
        # in from the parent trace
        # TODO: should compounds close over the trace where they were
        # defined?
        sp = value.makerNode.value
        if isinstance(sp, CompoundSP):
          sp = CompoundSP(sp.params, sp.exp, env)
        elif hasattr(sp, 'helper_trace'):
          sp = sp.__class__(sp.helper_trace.copy())
        self.trace.register_constant(addr, sp)
        value = self.trace.register_made_sp(addr, sp)
      else:
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
    try:
      return (0, sp.apply(handle, addr, args))
    except Exception:
      print "Tried applying sp", sp_node.value, "defined at", str(sp_node.address)[0:40], "to", [n.value for n in args]
      raise

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

  def eval_request(self, addr, exp, env):
    value = self.trace.eval_request(addr, exp, env)
    return value

  def value_at(self, addr):
    value = self.trace.value_at(addr)
    return value

  # stub other methods, used by proc...
  def __getattr__(self, name):
    return getattr(self.trace, name)

class Regenerator(Evaluator):
  """Unevaluate and regenerate according to a scaffold."""

  def __init__(self, trace, scaffold, fragment=None):
    super(Regenerator, self).__init__(trace)
    self.scaffold = scaffold
    if fragment is None:
      fragment = {} # addr -> result value
    self.fragment = fragment

  def uneval_request(self, addr):
    (exp, env) = self.trace.requests[addr]
    weight = self.uneval_family(addr, exp, env)
    self.trace.unregister_request(addr)
    self.fragment[addr, 'request'] = (exp, env)
    return weight

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
      weight = 0
      fragment = value
    else:
      (weight, fragment) = kernel.extract(value, args)

    self.store_fragment(addr, sp, args, fragment)
    return weight

  def apply_sp(self, addr, sp_node, args):
    sp = sp_node.value
    handle = RegeneratingTraceHandle(
      self.trace, sp_node.address, self)

    kernel = self.scaffold.kernel_at(sp, handle, addr)
    if kernel is None:
      weight = 0
      value = self.retrieve_fragment(addr, sp, args)
    else:
      (weight, value) = kernel.regen(args)

    return (weight, value)

  def store_fragment(self, addr, sp, args, fragment):
    self.fragment[addr] = (fragment, sp, args)

  def retrieve_fragment(self, addr, sp, args):
    (fragment, old_sp, old_args) = self.fragment[addr]

    # consistency check
    # assert self.is_same_sp(sp, old_sp)
    # for (arg, old_arg) in zip(args, old_args):
    #   assert self.is_same_arg(arg, old_arg)

    return fragment

  def is_same_sp(self, sp, old_sp):
    if sp is old_sp:
      return True
    if (isinstance(sp, CompoundSP) and
        isinstance(old_sp, CompoundSP) and
        sp.params == old_sp.params and
        sp.exp == old_sp.exp and
        sp.env is old_sp.env):
      return True
    return False

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

  def restore_request(self, addr):
    (exp, env) = self.fragment[addr, 'request']
    self.trace.register_request(addr, exp, env)
    return self.eval_family(addr, exp, env)

  def apply_sp(self, addr, sp_node, args):
    sp = sp_node.value
    handle = RegeneratingTraceHandle(
      self.trace, sp_node.address, self)

    kernel = self.scaffold.kernel_at(sp, handle, addr)
    fragment = self.retrieve_fragment(addr, sp, args)
    if kernel is None:
      value = fragment
    else:
      value = kernel.restore(args, fragment)

    return (0, value)


class RegeneratingTraceHandle(TraceHandle):
  def __init__(self, trace, sp_addr, regenerator):
    super(RegeneratingTraceHandle, self).__init__(
      trace, sp_addr)
    self.regenerator = regenerator

  def uneval_request(self, addr):
    w = self.regenerator.uneval_request(addr)
    assert w == 0

  def restore_request(self, addr):
    w, value = self.regenerator.restore_request(addr)
    assert w == 0
    return value


# TODO maybe move this to a separate file

# TODO if there are going to be a lot of these, maybe abstract the
# traversal itself so we don't have to subclass Regenerator all the
# time?
class WeightBounder(Regenerator):
  def unapply_sp(self, addr, value, sp_node, args):
    sp = sp_node.value
    fragment = value
    self.store_fragment(addr, sp, args, fragment)
    return 0

  def apply_sp(self, addr, sp_node, args):
    sp = sp_node.value
    handle = RegeneratingTraceHandle(
      self.trace, sp_node.address, self)

    kernel = self.scaffold.kernel_at(sp, handle, addr)
    if kernel is None:
      weight = 0
    else:
      weight = kernel.weight_bound(args)
    value = self.retrieve_fragment(addr, sp, args)

    return (weight, value)
