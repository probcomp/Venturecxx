import copy
import random
import numpy as np

import venture.mite.address as addresses
import venture.lite.types as t
import venture.lite.exp as e
from venture.lite.env import VentureEnvironment, EnvironmentType
from venture.lite.value import SPRef

from venture.untraced.node import Node, normalize

from venture.mite.evaluator import Evaluator
from venture.mite.sp import VentureSP, SimulationSP
from venture.mite.sp_registry import registerBuiltinSP
from venture.mite.sps.compound import CompoundSP

class BlankTraceSP(SimulationSP):
  def simulate(self, args):
    seed = args.py_prng().randint(1, 2**31 - 1)
    return t.Blob.asVentureValue(BlankTrace(seed))

class TraceActionSP(SimulationSP):
  arg_types = []
  result_type = t.Nil

  def simulate(self, args):
    values = args.operandValues()
    trace = t.Blob.asPython(values[0])
    args = [arg_t.asPython(value) for arg_t, value in
            zip(self.arg_types, values[1:])]
    result = self.do_action(trace, *args)
    return t.Pair(self.result_type, t.Blob).asVentureValue(result)

  def do_action(self, trace, *args):
    raise NotImplementedError

class NextBaseAddressSP(TraceActionSP):
  result_type = t.Blob

  def do_action(self, trace):
    trace = copy.copy(trace)
    address = trace.next_base_address()
    return address, trace

class GlobalEnvSP(TraceActionSP):
  result_type = EnvironmentType()

  def do_action(self, trace):
    return trace.global_env, trace

class EvalRequestSP(TraceActionSP):
  arg_types = [t.Blob, t.Exp, EnvironmentType()]

  def do_action(self, trace, addr, expr, env):
    trace = copy.deepcopy(trace)
    trace.eval_request(addr, expr, env)
    return None, trace

class BindGlobalSP(TraceActionSP):
  arg_types = [t.Symbol, t.Blob]

  def do_action(self, trace, symbol, addr):
    trace = copy.deepcopy(trace)
    trace.bind_global(symbol, addr)
    return None, trace

class RegisterObservationSP(TraceActionSP):
  arg_types = [t.Blob, t.Object]

  def do_action(self, trace, addr, value):
    trace = copy.deepcopy(trace)
    trace.register_observation(addr, value)
    return None, trace

class CheckConsistentSP(TraceActionSP):
  result_type = t.Bool

  def do_action(self, trace):
    return trace.check_consistent(), trace

class SplitTraceSP(TraceActionSP):
  result_type = t.Blob

  def do_action(self, trace):
    new_trace = copy.copy(trace)
    new_trace.reseed(trace)
    return new_trace, trace

registerBuiltinSP("blank_trace", BlankTraceSP())
registerBuiltinSP("next_base_address_f", NextBaseAddressSP())
registerBuiltinSP("global_env_f", GlobalEnvSP())
registerBuiltinSP("eval_request_f", EvalRequestSP())
registerBuiltinSP("bind_global_f", BindGlobalSP())
registerBuiltinSP("register_observation_f", RegisterObservationSP())
registerBuiltinSP("check_consistent_f", CheckConsistentSP())
registerBuiltinSP("split_trace_f", SplitTraceSP())

class ITrace(object):
  # external trace interface exposed to VentureScript

  def __init__(self):
    self.global_env = None

  def reseed(self, other_trace):
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
      addr = addresses.builtin(name)
      self.register_constant(addr, sp)
      value = self.register_made_sp(addr, sp)
      builtin_env.addBinding(name, Node(addr, value))
    return builtin_env

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
    self.register_response(addr, value)
    return (weight, value)

  def bind_global(self, symbol, addr):
    value = self.value_at(addr)
    self.global_env.addBinding(symbol, Node(addr, value))

  # remainder of the interface, to be implemented by subclasses

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

  def register_observation(self, addr, value):
    raise NotImplementedError

  def value_at(self, addr):
    raise NotImplementedError

  def check_consistent(self):
    raise NotImplementedError


class BlankTrace(AbstractTrace):
  def __init__(self, seed):
    super(BlankTrace, self).__init__(seed)
    self.results = {}
    self.observations = {}

  def register_request(self, addr, exp, env): pass

  def register_response(self, addr, value):
    self.results[addr] = value

  def register_constant(self, addr, value): pass
  def register_lookup(self, addr, orig_addr): pass
  def register_application(self, addr, arity, value): pass
  def register_made_sp(self, addr, sp): return SPRef((addr, sp))
  def deref_sp(self, sp_node):
    (addr, sp) = sp_node.value.makerNode
    return Node(addr, sp)

  def register_observation(self, addr, value):
    self.observations[addr] = value

  def value_at(self, addr):
    return self.results[addr]

  def check_consistent(self):
    return all(self.results[id] == self.observations[id]
               for id in self.observations)


