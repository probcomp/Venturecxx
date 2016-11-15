import venture.lite.types as t

from venture.mite.sp import SimulationSP
from venture.mite.sp_registry import registerBuiltinSP


def register_trace_type(name, cls, actions):
  constructor = TraceConstructorSP(cls)
  registerBuiltinSP(name, constructor)
  for action_name, action_sp in actions.iteritems():
    action_func_name = action_name + "_func"
    registerBuiltinSP(action_func_name, action_sp)
    (params, body) = action_sp.action_defn(action_func_name)
    body = t.Exp.asPython(t.Exp.asVentureValue(body))
    registerBuiltinSP(action_name, (params, body))


class TraceConstructorSP(SimulationSP):
  def __init__(self, trace_class):
    self.trace_class = trace_class

  def simulate(self, inputs, _prng):
    assert len(inputs) == 0
    return t.Blob.asVentureValue(self.trace_class())


class TracePropertySP(SimulationSP):
  def __init__(self, property_name, property_type):
    self.name = property_name
    self.output_type = property_type

  def simulate(self, inputs, _prng):
    assert len(inputs) == 1
    trace = t.Blob.asPython(inputs[0])
    output = getattr(trace, self.name)
    return t.Pair(self.output_type, t.Blob).asVentureValue(
      (output, trace))

  def is_deterministic(self):
    return True

  def action_defn(self, action_func_name):
    # interpreted by register_trace_type
    return ([], ['inference_action', action_func_name])

trace_property = TracePropertySP


# TODO: this should have an unapply method that undoes its effect on
# the trace.
class TraceActionSP(SimulationSP):
  def __init__(self, method_name, input_types, output_type, deterministic=False):
    self.name = method_name
    self.input_types = input_types
    self.output_type = output_type
    self.deterministic = deterministic

  def simulate(self, inputs, _prng):
    assert len(inputs) == 1 + len(self.input_types)
    trace = t.Blob.asPython(inputs[0])
    inputs = [in_t.asPython(value) for in_t, value in
              zip(self.input_types, inputs[1:])]
    output = getattr(trace, self.name)(*inputs)
    # print "Tried to do trace action", self.name, "on", inputs, "got", output
    return t.Pair(self.output_type, t.Blob).asVentureValue(
      (output, trace))

  def is_deterministic(self):
    return self.deterministic

  def action_defn(self, action_func_name):
    # interpreted by register_trace_type
    names = ['var{}'.format(i) for i in range(len(self.input_types))]
    return (names,
            ['inference_action',
             ['make_csp', ['quote', ['trace']],
              ['quote', [action_func_name, 'trace'] + names]]])

trace_action = TraceActionSP
