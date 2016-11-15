from venture.lite.env import VentureEnvironment
import venture.lite.types as t

from venture.untraced.node import Node

from venture.mite.sp import SimulationSP
from venture.mite.sp_registry import registerBuiltinSP
from venture.mite.traces import BlankTrace

class MakeSimulationSP(SimulationSP):
  def simulate(self, inputs, prng):
    constructor = t.Exp.asPython(inputs[0])
    ctor_inputs = inputs[1:]
    seed = prng.py_prng.randint(1, 2**31 - 1)
    helper_trace = BlankTrace(seed)
    addr = helper_trace.next_base_address()
    names = ['var{}'.format(i) for i in range(len(ctor_inputs))]
    values = [Node(None, val) for val in ctor_inputs]
    expr = [constructor] + names
    env = VentureEnvironment(helper_trace.global_env, names, values)
    helper_trace.eval_request(addr, expr, env)
    helper_trace.bind_global("the_sp", addr)
    return MadeSimulationSP(helper_trace)

  def log_density(self, _value, _inputs):
    # XXX Assumes the value is what the application actually produced.
    # I can't even fix this by rerunning the simulation function,
    # because equality testing of SRRefs relies on object identity.
    return 0

  def is_deterministic(self):
    return True


class MadeSimulationSP(SimulationSP):
  def __init__(self, helper_trace):
    self.helper_trace = helper_trace

  def simulate(self, inputs, _prng):
    return self.run_in_helper_trace('simulate', inputs)

  def log_density(self, output, inputs):
    logp = self.run_in_helper_trace('log_density', [output] + inputs)
    return t.Number.asPython(logp)

  def is_deterministic(self):
    if self.has_method('is_deterministic'):
      self.run_in_helper_trace('is_deterministic', [])
    else:
      return False

  def incorporate(self, output, inputs):
    if self.has_method('incorporate'):
      self.run_in_helper_trace('incorporate', [output] + inputs)

  def unincorporate(self, output, inputs):
    if self.has_method('unincorporate'):
      self.run_in_helper_trace('unincorporate', [output] + inputs)

  def has_method(self, method):
    helper_trace = self.helper_trace
    addr = helper_trace.next_base_address()
    expr = ['contains', 'the_sp', ['quote', method]]
    env = VentureEnvironment(helper_trace.global_env)
    value = helper_trace.eval_request(addr, expr, env)
    return value.getBool()

  def run_in_helper_trace(self, method, inputs):
    helper_trace = self.helper_trace
    addr = helper_trace.next_base_address()
    names = ['var{}'.format(i) for i in range(len(inputs))]
    values = [Node(None, val) for val in inputs]
    expr = ['first',
            [['action_func',
              [['lookup', 'the_sp', ['quote', method]]] + names],
             ['lookup', 'the_sp', ['quote', 'state']]]]
    env = VentureEnvironment(helper_trace.global_env, names, values)
    value = helper_trace.eval_request(addr, expr, env)
    return value

# TODO: rename to "elementary" SP everywhere
# (including the "SimulationSP" class itself)
registerBuiltinSP("make_simulation_sp", MakeSimulationSP())
registerBuiltinSP("_make_elementary_sp", MakeSimulationSP())
