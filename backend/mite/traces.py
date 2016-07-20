import copy
import random
import numpy as np

from collections import OrderedDict

import venture.mite.address as addresses
import venture.lite.types as t
import venture.lite.exp as e
from venture.lite.env import VentureEnvironment, EnvironmentType
from venture.lite.value import SPRef

from venture.untraced.node import Node, normalize

from venture.mite.evaluator import Evaluator, Regenerator, Restorer
from venture.mite.sp import VentureSP, SimulationSP
from venture.mite.sp_registry import registerBuiltinSP
from venture.mite.sps.compound import CompoundSP
from venture.mite.state import (register_trace_type,
                                trace_property,
                                trace_action,
                                TraceConstructorSP)


class ITrace(object):
  # external trace interface exposed to VentureScript

  def __init__(self):
    self.global_env = None

  def copy(self):
    raise NotImplementedError

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

  def check_consistent(self):
    raise NotImplementedError

  def extract(self, subproblem):
    raise NotImplementedError

  def regen(self, subproblem, trace_fragment):
    raise NotImplementedError

  def restore(self, subproblem, trace_fragment):
    raise NotImplementedError


class AbstractTrace(ITrace):
  # common implementation of trace interface
  # defines internal interface for concrete trace representations

  def __init__(self, seed):
    super(AbstractTrace, self).__init__()
    prng = random.Random(seed)
    self.np_prng = np.random.RandomState(prng.randint(1, 2**31 - 1))
    self.py_prng = random.Random(prng.randint(1, 2**31 - 1))
    self.directive_counter = 0
    self.global_env = VentureEnvironment(self.builtin_environment())

  def builtin_environment(self):
    from venture.mite.builtin import builtInSPs
    from venture.mite.builtin import builtInValues
    builtin_env = VentureEnvironment()
    for name, value in builtInValues().iteritems():
      addr = addresses.builtin(name)
      self.register_constant(addr, value)
      builtin_env.addBinding(name, Node(addr, value))
    for name, sp in builtInSPs().iteritems():
      if isinstance(sp, tuple):
        # assume compound definition
        # TODO define a namedtuple?
        (params, body) = sp
        sp = CompoundSP(params, body, builtin_env)
      addr = addresses.builtin(name)
      self.register_constant(addr, sp)
      value = self.register_made_sp(addr, sp)
      builtin_env.addBinding(name, Node(addr, value))
    return builtin_env

  def copy(self):
    new_trace = copy.deepcopy(self)
    new_trace.reseed(self)
    return new_trace

  def reseed(self, other):
    prng = other.py_prng
    self.np_prng = np.random.RandomState(prng.randint(1, 2**31 - 1))
    self.py_prng = random.Random(prng.randint(1, 2**31 - 1))

  def next_base_address(self):
    self.directive_counter += 1
    return addresses.directive(self.directive_counter)

  def eval_request(self, addr, exp, env):
    self.register_request(addr, exp, env)
    weight, value = Evaluator(self).eval_family(addr, exp, env)
    return (weight, value)

  def bind_global(self, symbol, addr):
    value = self.value_at(addr)
    self.global_env.addBinding(symbol, Node(addr, value))

  # remainder of the interface, to be implemented by subclasses

  def register_request(self, addr, exp, env):
    raise NotImplementedError

  def register_constant(self, addr, value):
    raise NotImplementedError

  def register_lookup(self, addr, node):
    raise NotImplementedError

  def register_application(self, addr, arity, value):
    raise NotImplementedError

  def register_made_sp(self, addr, value):
    raise NotImplementedError

  def deref_sp(self, sp_ref):
    raise NotImplementedError

  def register_observation(self, addr, value):
    raise NotImplementedError

  def value_at(self, addr):
    raise NotImplementedError

  def check_consistent(self):
    raise NotImplementedError


class BlankTrace(AbstractTrace):
  """Record only the final results of requested expressions.

  This corresponds to "untraced" evaluation, and supports forward
  evaluation and rejection sampling only.

  """

  def __init__(self, seed):
    self.results = OrderedDict()
    self.observations = {}
    super(BlankTrace, self).__init__(seed)

  def register_request(self, addr, exp, env): pass

  def register_constant(self, addr, value):
    self.maybe_record_result(addr, value)

  def register_lookup(self, addr, node):
    self.maybe_record_result(addr, node.value)

  def register_application(self, addr, arity, value):
    self.maybe_record_result(addr, value)

  def maybe_record_result(self, addr, value):
    if isinstance(addr, (addresses.directive, addresses.request)):
      self.results[addr] = value

  def register_made_sp(self, addr, sp):
    ret = SPRef((addr, sp))
    if addr in self.results:
      assert self.results[addr] is sp
      self.results[addr] = ret
    return ret

  def deref_sp(self, sp_ref):
    (addr, sp) = sp_ref.makerNode
    return Node(addr, sp)

  def register_observation(self, addr, value):
    self.observations[addr] = value

  def value_at(self, addr):
    return self.results[addr]

  def check_consistent(self):
    return all(self.results[id] == self.observations[id]
               for id in self.observations)


class FlatTrace(AbstractTrace):
  """Maintain a flat lookup table of random choices, keyed by address.

  This corresponds to the "random database" implementation approach
  from Wingate et al (2011).

  """

  def __init__(self, seed):
    self.requests = {}
    self.results = OrderedDict()
    self.made_sps = {}
    self.observations = {}
    super(FlatTrace, self).__init__(seed)

  def register_request(self, addr, exp, env):
    self.requests[addr] = (exp, env)

  def register_constant(self, addr, value):
    self.results[addr] = value

  def register_lookup(self, addr, node):
    assert node.value is self.results[node.address]
    self.results[addr] = node.value

  def register_application(self, addr, arity, value):
    self.results[addr] = value

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

  def unregister_constant(self, addr):
    del self.results[addr]

  def unregister_lookup(self, addr):
    del self.results[addr]

  def unregister_application(self, addr):
    del self.results[addr]

  def unregister_made_sp(self, addr):
    sp = self.made_sps[addr]
    del self.made_sps[addr]
    self.results[addr] = sp
    return sp

  def select(self, _selector):
    from venture.mite.scaffold import DefaultAllScaffold
    return DefaultAllScaffold()

  def pyselect(self, code):
    from venture.mite.scaffold import MinimalScaffold
    selector = eval(code, vars(addresses))
    return MinimalScaffold(selector)

  def extract(self, subproblem):
    x = Regenerator(self, subproblem)
    weight = 0
    for i in reversed(range(self.directive_counter)):
      addr = addresses.directive(i+1)
      (exp, env) = self.requests[addr]
      weight += x.uneval_family(addr, exp, env)
    return (weight, x.fragment)

  def regen(self, subproblem, trace_fragment):
    x = Regenerator(self, subproblem, trace_fragment)
    weight = 0
    for i in range(self.directive_counter):
      addr = addresses.directive(i+1)
      (exp, env) = self.requests[addr]
      w, _ = x.eval_family(addr, exp, env)
      weight += w
    return weight

  def restore(self, subproblem, trace_fragment):
    x = Restorer(self, subproblem, trace_fragment)
    for i in range(self.directive_counter):
      addr = addresses.directive(i+1)
      (exp, env) = self.requests[addr]
      x.eval_family(addr, exp, env)


register_trace_type("_trace", ITrace, {
  "next_base_address": trace_action("next_base_address", [], t.Blob),
  "global_env": trace_property("global_env", EnvironmentType()),
  "eval_request": trace_action("eval_request", [t.Blob, t.Exp, EnvironmentType()], t.Nil),
  "bind_global": trace_action("bind_global", [t.Symbol, t.Blob], t.Nil),
  "register_observation": trace_action("register_observation", [t.Blob, t.Object], t.Nil),
  "value_at": trace_action("value_at", [t.Blob], t.Object),
  "check_consistent": trace_action("check_consistent", [], t.Bool),
  "split_trace": trace_action("copy", [], t.Blob),
  "select": trace_action("select", [t.Object], t.Blob),
  "pyselect": trace_action("pyselect", [t.String], t.Blob),
  "extract": trace_action("extract", [t.Blob], t.Pair(t.Number, t.Blob)),
  "regen": trace_action("regen", [t.Blob, t.Blob], t.Number),
  "restore": trace_action("restore", [t.Blob, t.Blob], t.Nil),
})


class VentureTraceConstructorSP(TraceConstructorSP):
  def simulate(self, _inputs, prng):
    seed = prng.py_prng.randint(1, 2**31 - 1)
    return t.Blob.asVentureValue(self.trace_class(seed))

registerBuiltinSP("blank_trace", VentureTraceConstructorSP(BlankTrace))
registerBuiltinSP("flat_trace", VentureTraceConstructorSP(FlatTrace))
