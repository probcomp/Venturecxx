import venture.lite.types as t

from venture.mite.sp import VentureSP, SimulationSP
from venture.mite.sp_registry import registerBuiltinSP


def register_subtrace_type(name, cls, actions):
  constructor = SubtraceConstructorSP(cls)
  registerBuiltinSP(name, constructor)
  for action_name, action_sp in actions.iteritems():
    registerBuiltinSP(action_name, action_sp)


class SubtraceConstructorSP(SimulationSP):
  def __init__(self, trace_class):
    self.trace_class = trace_class

  def simulate(self, inputs, _prng):
    assert len(inputs) == 0
    return t.Blob.asVentureValue(self.trace_class())


class SubtracePropertySP(SimulationSP):
  def __init__(self, property_name, property_type):
    self.name = property_name
    self.output_type = property_type

  def simulate(self, inputs, _prng):
    assert len(inputs) == 1
    trace = t.Blob.asPython(inputs[0])
    output = getattr(trace, self.name)
    return t.Pair(self.output_type, t.Blob).asVentureValue(
      (output, trace))

subtrace_property = SubtracePropertySP


# TODO: this should have an unapply method that undoes its effect on
# the trace.
class SubtraceActionSP(SimulationSP):
  def __init__(self, method_name, input_types, output_type):
    self.name = method_name
    self.input_types = input_types
    self.output_type = output_type

  def simulate(self, inputs, _prng):
    assert len(inputs) == 1 + len(self.input_types)
    trace = t.Blob.asPython(inputs[0])
    inputs = [in_t.asPython(value) for in_t, value in
              zip(self.input_types, inputs[1:])]
    output = getattr(trace, self.name)(*inputs)
    return t.Pair(self.output_type, t.Blob).asVentureValue(
      (output, trace))

subtrace_action = SubtraceActionSP
