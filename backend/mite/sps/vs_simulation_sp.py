from venture.lite.env import VentureEnvironment
from venture.lite.exception import VentureError
import venture.lite.types as t

from venture.untraced.node import Node

from venture.mite.sp_registry import registerBuiltinSP
from venture.mite.sp import SimulationSP
from venture.mite.traces import BlankTrace

class MakeSimulationSP(SimulationSP):
  def simulate(self, inputs, prng):
    assert len(inputs) == 1
    defns = t.List(t.Exp).asPython(inputs[0])
    seed = prng.py_prng.randint(1, 2**31 - 1)
    helper_trace = BlankTrace(seed)
    for name, expr in defns:
      addr = helper_trace.next_base_address()
      helper_trace.eval_request(addr, expr, helper_trace.global_env)
      helper_trace.bind_global(name, addr)
    return MadeSimulationSP(helper_trace)

class MadeSimulationSP(SimulationSP):
  def __init__(self, helper_trace):
    self.helper_trace = helper_trace

  def simulate(self, inputs, _prng):
    return self.run_in_helper_trace('simulate', inputs)

  def logDensity(self, output, inputs):
    logp = self.run_in_helper_trace('log_density', [output] + inputs)
    return t.Number.asPython(logp)

  def incorporate(self, output, inputs):
    self.run_in_helper_trace('incorporate', [output] + inputs)

  def unincorporate(self, output, inputs):
    self.run_in_helper_trace('unincorporate', [output] + inputs)

  def run_in_helper_trace(self, method, inputs):
    helper_trace = self.helper_trace
    addr = helper_trace.next_base_address()
    names = ['var{}'.format(i) for i in range(len(inputs))]
    values = [Node(None, val) for val in inputs]
    expr = ['first', [['action_func', [method] + names], 'trace']]
    env = VentureEnvironment(helper_trace.global_env, names, values)
    w, value = helper_trace.eval_request(addr, expr, env)
    assert w == 0
    return value

registerBuiltinSP("make_simulation_sp", MakeSimulationSP())
