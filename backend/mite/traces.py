import copy
import random
import numpy as np

from venture.lite.address import Address, List
import venture.lite.types as t
import venture.lite.exp as e
from venture.lite.env import VentureEnvironment
from venture.lite.value import SPRef

from venture.untraced.node import Node, normalize

from venture.mite.sp import VentureSP, SimulationSP
from venture.mite.sp_registry import registerBuiltinSP
from venture.mite.sps.compound import CompoundSP

class TracePropertySP(SimulationSP):
  def simulate(self, args):
    values = args.operandValues()
    trace = t.Blob.asPython(values[0])
    prop_name = t.Symbol.asPython(values[1])
    result = getattr(trace, prop_name)
    return t.Pair(t.Blob, t.Blob).asVentureValue((result, trace))

class TraceActionSP(SimulationSP):
  def simulate(self, args):
    values = args.operandValues()
    trace = copy.deepcopy(t.Blob.asPython(values[0]))
    method_name = t.Symbol.asPython(values[1])
    def unbox(x):
      if x in t.Blob:
        return t.Blob.asPython(x)
      else:
        return t.Exp.asPython(x)
    args = map(unbox, values[2:])
    method = getattr(trace, method_name)
    result = method(*args)
    return t.Pair(t.Blob, t.Blob).asVentureValue((result, trace))

class BlankTraceSP(SimulationSP):
  def simulate(self, args):
    seed = args.py_prng().randint(1, 2**31 - 1)
    return t.Blob.asVentureValue(BlankTrace(seed))

registerBuiltinSP("trace_property", TracePropertySP())
registerBuiltinSP("trace_action", TraceActionSP())
registerBuiltinSP("blank_trace", BlankTraceSP())

class ITrace(object):
  # external trace interface exposed to VentureScript

  def __init__(self):
    self.global_env = None

  def next_base_address(self):
    raise NotImplementedError

  def eval_request(self, address, expression, environment):
    raise NotImplementedError

  def bind_global(self, symbol, address):
    raise NotImplementedError

  def register_observation(self, address, value):
    raise NotImplementedError

  def value_at(self, address):
    raise NotImplementedError

class AbstractTrace(ITrace):
  # common implementation of trace interface
  # defines internal interface for concrete trace representations

  def __init__(self, seed):
    super(AbstractTrace, self).__init__()
    rng = random.Random(seed)
    self.np_prng = np.random.RandomState(rng.randint(1, 2**31 - 1))
    self.py_prng = random.Random(rng.randint(1, 2**31 - 1))
    self.directive_counter = 0
    self.global_env = VentureEnvironment(self.builtin_environment())

  def builtin_environment(self):
    from venture.mite.builtin import builtInSPs
    from venture.mite.builtin import builtInValues
    builtin_env = VentureEnvironment()
    for name, value in builtInValues().iteritems():
      addr = Address(List(name))
      self.register_constant(addr, value)
      builtin_env.addBinding(name, Node(addr, value))
    for name, sp in builtInSPs().iteritems():
      addr = Address(List(name))
      self.register_constant(addr, sp)
      value = self.register_made_sp(addr, sp)
      builtin_env.addBinding(name, Node(addr, value))
    return builtin_env

  def next_base_address(self):
    self.directive_counter += 1
    return Address(List(self.directive_counter))

  def eval_request(self, addr, exp, env):
    self.register_request(addr, exp, env)
    weight, value = self.eval_family(addr, exp, env)
    self.register_response(addr, value)
    return (weight, value)

  def eval_family(self, addr, exp, env):
    weight = 0
    value = None

    if e.isVariable(exp):
      result_node = env.findSymbol(exp)
      self.register_lookup(addr, result_node.address)
      value = result_node.value
    elif e.isSelfEvaluating(exp):
      value = normalize(exp)
      self.register_constant(addr, value)
    elif e.isQuotation(exp):
      value = normalize(e.textOfQuotation(exp))
      self.register_constant(addr, value)
    elif e.isLambda(exp):
      (params, body) = e.destructLambda(exp)
      sp = CompoundSP(params, body, env)
      self.register_constant(addr, sp)
      value = self.register_made_sp(addr, sp)
    else:
      # SP application
      nodes = []
      for index, subexp in enumerate(exp):
        subaddr = addr.extend(index)
        w, v = self.eval_family(subaddr, subexp, env)
        weight += w
        nodes.append(Node(subaddr, v))

      sp_node = self.deref_sp(nodes[0])
      args = nodes[1:]

      handle = self.construct_trace_handle(addr, sp_node, args)
      w, value = self.apply_sp(sp_node.value, handle)
      weight += w

      self.register_application(addr, len(exp), value)
      if isinstance(value, VentureSP):
        value = self.register_made_sp(addr, value)

    return (weight, value)

  def register_request(self, addr, exp, env):
    raise NotImplementedError

  def register_response(self, addr, value):
    raise NotImplementedError

  def register_constant(self, addr, value):
    raise NotImplementedError

  def register_lookup(self, addr, orig_addr):
    raise NotImplementedError

  def register_application(self, addr, arity, value):
    raise NotImplementedError

  def register_made_sp(self, addr, value):
    raise NotImplementedError

  def deref_sp(self, sp):
    raise NotImplementedError

  def construct_trace_handle(self, app_addr, sp_addr, args):
    # TODO: remove the Args struct and this method
    raise NotImplementedError

  def apply_sp(self, sp, args):
    raise NotImplementedError

  def bind_global(self, symbol, addr):
    value = self.value_at(addr)
    self.global_env.addBinding(symbol, Node(addr, value))

  def register_observation(self, exp, value):
    raise NotImplementedError

  def value_at(self, addr):
    raise NotImplementedError


class BlankTrace(AbstractTrace):
  def __init__(self, seed):
    super(BlankTrace, self).__init__(seed)
    self.results = {}

  def register_request(self, addr, exp, env): pass

  def register_response(self, addr, value):
    assert addr.last.rest.isEmpty()
    base_id = addr.last.last
    self.results[base_id] = value

  def register_constant(self, addr, value): pass
  def register_lookup(self, addr, orig_addr): pass
  def register_application(self, addr, arity, value): pass
  def register_made_sp(self, addr, sp): return SPRef((addr, sp))
  def deref_sp(self, sp_node):
    (addr, sp) = sp_node.value.makerNode
    return Node(addr, sp)

  def construct_trace_handle(self, app_addr, sp_addr, args):
    return TraceHandle(self, app_addr, sp_addr, args)

  def apply_sp(self, sp, args):
    return (0, sp.apply(args))

  def register_observation(self, exp, value):
    raise NotImplementedError

  def value_at(self, addr):
    assert addr.last.rest.isEmpty()
    base_id = addr.last.last
    return self.results[base_id]


# TODO: this signature retains backward compatibility with Args for now,
# but we should remove that
from venture.lite.psp import IArgs
class TraceHandle(IArgs):
  def __init__(self, trace, app_addr, sp_addr, args):
    self.trace = trace
    self.app_addr = self.node = app_addr
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
    return self.app_addr.request(List((self.sp_addr, request_id)))

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
