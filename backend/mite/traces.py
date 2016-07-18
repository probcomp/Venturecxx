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

from venture.mite.evaluator import Evaluator, Regenerator
from venture.mite.sp import VentureSP, SimulationSP
from venture.mite.sp_registry import registerBuiltinSP
from venture.mite.sps.compound import CompoundSP

class BlankTraceSP(SimulationSP):
  def simulate(self, _inputs, prng):
    seed = prng.py_prng.randint(1, 2**31 - 1)
    return t.Blob.asVentureValue(BlankTrace(seed))

class FlatTraceSP(SimulationSP):
  def simulate(self, _inputs, prng):
    seed = prng.py_prng.randint(1, 2**31 - 1)
    return t.Blob.asVentureValue(FlatTrace(seed))

class TraceActionSP(SimulationSP):
  arg_types = []
  result_type = t.Nil

  def simulate(self, inputs, _prng):
    trace = t.Blob.asPython(inputs[0])
    args = [arg_t.asPython(value) for arg_t, value in
            zip(self.arg_types, inputs[1:])]
    result = self.do_action(trace, *args)
    return t.Pair(self.result_type, t.Blob).asVentureValue(result)

  def do_action(self, trace, *args):
    raise NotImplementedError

class NextBaseAddressSP(TraceActionSP):
  result_type = t.Blob

  def do_action(self, trace):
    address = trace.next_base_address()
    return address, trace

class GlobalEnvSP(TraceActionSP):
  result_type = EnvironmentType()

  def do_action(self, trace):
    return trace.global_env, trace

class EvalRequestSP(TraceActionSP):
  arg_types = [t.Blob, t.Exp, EnvironmentType()]

  def do_action(self, trace, addr, expr, env):
    trace.eval_request(addr, expr, env)
    return None, trace

class BindGlobalSP(TraceActionSP):
  arg_types = [t.Symbol, t.Blob]

  def do_action(self, trace, symbol, addr):
    trace.bind_global(symbol, addr)
    return None, trace

class RegisterObservationSP(TraceActionSP):
  arg_types = [t.Blob, t.Object]

  def do_action(self, trace, addr, value):
    trace.register_observation(addr, value)
    return None, trace

class ValueAtSP(TraceActionSP):
  arg_types = [t.Blob]
  result_type = t.Object

  def do_action(self, trace, addr):
    return trace.value_at(addr), trace

class CheckConsistentSP(TraceActionSP):
  result_type = t.Bool

  def do_action(self, trace):
    return trace.check_consistent(), trace

class SplitTraceSP(TraceActionSP):
  result_type = t.Blob

  def do_action(self, trace):
    new_trace = trace.copy()
    return new_trace, trace

class ExtractSP(TraceActionSP):
  arg_types = [t.Object] ## TODO take a subproblem selector
  result_type = t.Pair(t.Number, t.Blob)

  def do_action(self, trace, subproblem):
    (weight, trace_frag) = trace.extract(subproblem)
    return (weight, trace_frag), trace

class RegenSP(TraceActionSP):
  arg_types = [t.Object] ## TODO take a subproblem selector
  result_type = t.Number

  def do_action(self, trace, subproblem):
    weight = trace.regen(subproblem)
    return weight, trace

class RestoreSP(TraceActionSP):
  arg_types = [t.Object, t.Blob] ## TODO take a subproblem selector

  def do_action(self, trace, subproblem, trace_frag):
    trace.restore(subproblem, trace_frag)
    return None, trace

registerBuiltinSP("blank_trace", BlankTraceSP())
registerBuiltinSP("flat_trace", FlatTraceSP())
registerBuiltinSP("next_base_address_f", NextBaseAddressSP())
registerBuiltinSP("global_env_f", GlobalEnvSP())
registerBuiltinSP("eval_request_f", EvalRequestSP())
registerBuiltinSP("bind_global_f", BindGlobalSP())
registerBuiltinSP("register_observation_f", RegisterObservationSP())
registerBuiltinSP("value_at_f", ValueAtSP())
registerBuiltinSP("check_consistent_f", CheckConsistentSP())
registerBuiltinSP("split_trace_f", SplitTraceSP())
registerBuiltinSP("extract_f", ExtractSP())
registerBuiltinSP("regen_f", RegenSP())
registerBuiltinSP("restore_f", RestoreSP())

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

  def regen(self, subproblem):
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

  def extract(self, subproblem):
    x = Regenerator(self)
    weight = 0
    for i in reversed(range(self.directive_counter)):
      addr = addresses.directive(i+1)
      (exp, env) = self.requests[addr]
      weight += x.uneval_family(addr, exp, env)
    return (weight, x.fragment)

  def regen(self, subproblem):
    x = Evaluator(self)
    weight = 0
    for i in range(self.directive_counter):
      addr = addresses.directive(i+1)
      (exp, env) = self.requests[addr]
      w, _ = x.eval_family(addr, exp, env)
      weight += w
    return weight

  def restore(self, subproblem, trace_fragment):
    x = Regenerator(self, trace_fragment)
    for i in range(self.directive_counter):
      addr = addresses.directive(i+1)
      (exp, env) = self.requests[addr]
      x.eval_family(addr, exp, env)
