from venture.lite.env import VentureEnvironment
import venture.lite.types as t

from venture.untraced.node import Node

from venture.mite.address import VentureAddressed
from venture.mite.sp import ApplicationKernel
from venture.mite.sp import SimulationSP
from venture.mite.sp import VentureSP
from venture.mite.sp_registry import registerBuiltinSP
from venture.mite.traces import BlankTrace

class MakeFullSP(VentureSP):
  def apply(self, trace_handle, app_id, inputs):
    constructor = t.Exp.asPython(inputs[0].value)
    ctor_inputs = inputs[1:]
    seed = trace_handle.py_prng().randint(1, 2**31 - 1)
    helper_trace = BlankTrace(seed)
    addr = helper_trace.next_base_address()
    names = ['var{}'.format(i) for i in range(len(ctor_inputs))]
    values = [Node(None, VentureAddressed(arg, arg.value))
              for arg in ctor_inputs]
    expr = [constructor] + names
    env = VentureEnvironment(helper_trace.global_env, names, values)
    helper_trace.eval_request(addr, expr, env)
    helper_trace.bind_global("the_sp", addr)
    return MadeFullSP(helper_trace)

class MadeFullSP(VentureSP):
  def __init__(self, helper_trace):
    self.helper_trace = helper_trace

  def apply(self, trace_handle, app_id, inputs):
    handle = t.Blob.asVentureValue(trace_handle)
    app_id = t.Blob.asVentureValue(app_id)
    inputs = [node.value for node in inputs] # TODO expose refs
    return self.run_in_helper_trace('apply', [handle, app_id] + inputs)

  def log_density(self, output, inputs):
    logp = self.run_in_helper_trace('log_density', [output] + inputs)
    return t.Number.asPython(logp)

  def proposal_kernel(self, trace_handle, app_id):
    handle = t.Blob.asVentureValue(trace_handle)
    app_id = t.Blob.asVentureValue(app_id)
    kernel_dict = self.run_in_helper_trace('proposal_kernel', [handle, app_id])
    return ProxyKernel(self.helper_trace, kernel_dict)

  def constraint_kernel(self, trace_handle, app_id, val):
    handle = t.Blob.asVentureValue(trace_handle)
    app_id = t.Blob.asVentureValue(app_id)
    # TODO detect absence of a method definition more reliably
    try:
      kernel_dict = self.run_in_helper_trace('constraint_kernel', [handle, app_id, val])
      return ProxyKernel(self.helper_trace, kernel_dict)
    except KeyError:
      return NotImplemented

  def propagating_kernel(self, trace_handle, app_id, parent):
    handle = t.Blob.asVentureValue(trace_handle)
    app_id = t.Blob.asVentureValue(app_id)
    parent = t.Blob.asVentureValue(parent)
    kernel_dict = self.run_in_helper_trace('propagating_kernel', [handle, app_id, parent])
    return ProxyKernel(self.helper_trace, kernel_dict)

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

class ProxyKernel(ApplicationKernel):
  def __init__(self, helper_trace, kernel_dict):
    self.helper_trace = helper_trace
    self.kernel_dict = kernel_dict
    self.env = VentureEnvironment(helper_trace.global_env,
      ['the_kernel'], [Node(None, kernel_dict)])

  def extract(self, output, inputs):
    inputs = [node.value for node in inputs] # TODO expose refs
    result = self.run_in_helper_trace('extract', [output] + inputs)
    return t.Pair(t.Number, t.Object).asPython(result)

  def regen(self, inputs):
    inputs = [node.value for node in inputs] # TODO expose refs
    result = self.run_in_helper_trace('regen', inputs)
    return t.Pair(t.Number, t.Object).asPython(result)

  def restore(self, inputs, trace_frag):
    inputs = [node.value for node in inputs] # TODO expose refs
    return self.run_in_helper_trace('restore', inputs + [trace_frag])

  def run_in_helper_trace(self, method, inputs):
    helper_trace = self.helper_trace
    addr = helper_trace.next_base_address()
    names = ['var{}'.format(i) for i in range(len(inputs))]
    values = [Node(None, val) for val in inputs]
    expr = ['first',
            [['action_func',
              [['lookup', 'the_kernel', ['quote', method]]] + names],
             ['lookup', 'the_sp', ['quote', 'state']]]]
    env = VentureEnvironment(self.env, names, values)
    value = helper_trace.eval_request(addr, expr, env)
    return value

registerBuiltinSP("make_full_sp", MakeFullSP())
registerBuiltinSP("_make_sp", MakeFullSP())
