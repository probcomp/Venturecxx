from venture.lite.exception import VentureBuiltinSPMethodError
from venture.lite.utils import override
from venture.lite.value import VentureValue, VentureNil
import venture.value.dicts as v

class VentureSP(VentureValue):
  """A stochastic procedure."""

  def apply(self, _trace_handle, _application_id, _inputs):
    raise VentureBuiltinSPMethodError("Apply not implemented!")

  def unapply(self, _trace_handle, _application_id, _output, _inputs):
    raise VentureBuiltinSPMethodError("Cannot unapply")

  def restore(self, _trace_handle, _application_id, _inputs, _trace_fragment):
    raise VentureBuiltinSPMethodError("Cannot restore previous state")

  def logDensity(self, _value, _inputs):
    raise VentureBuiltinSPMethodError("Cannot assess log density")

  def proposal_kernel(self, trace_handle, application_id):
    return DefaultProposalKernel(self, trace_handle, application_id)

  def constrained_kernel(self, _trace_handle, _application_id, _val):
    return NotImplemented

  def show(self):
    return "<procedure>"

  def extractStateAsVentureValue(self):
    return VentureNil()

  def asStackDict(self, _trace=None):
    return v.sp(self.show(), self.extractStateAsVentureValue().asStackDict())

class ApplicationKernel(object):
  def extract(self, _output, _inputs):
    raise VentureBuiltinSPMethodError("Extract not implemented")

  def regen(self, _inputs):
    raise VentureBuiltinSPMethodError("Regen not implemented")

  def restore(self, _inputs, _trace_fragment):
    raise VentureBuiltinSPMethodError("Restore not implemented")

class DefaultProposalKernel(ApplicationKernel):
  def __init__(self, sp, trace_handle, application_id):
    self.sp = sp
    self.trace_handle = trace_handle
    self.application_id = application_id

  def extract(self, output, inputs):
    return (0, self.sp.unapply(
      self.trace_handle, self.application_id, output, inputs))

  def regen(self, inputs):
    return (0, self.sp.apply(
      self.trace_handle, self.application_id, inputs))

  def restore(self, inputs, trace_fragment):
    return self.sp.restore(
      self.trace_handle, self.application_id, inputs, trace_fragment)


class SimulationSP(VentureSP):
  @override(VentureSP)
  def apply(self, trace_handle, _application_id, inputs):
    # TODO: use trace_handle.value_at to unpack the input nodes
    input_values = [node.value for node in inputs]
    output = self.simulate(input_values, trace_handle.prng())
    self.incorporate(output, input_values)
    return output

  @override(VentureSP)
  def unapply(self, _trace_handle, _application_id, output, inputs):
    input_values = [node.value for node in inputs]
    self.unincorporate(output, input_values)
    return output

  @override(VentureSP)
  def restore(self, _trace_handle, _application_id, inputs, output):
    input_values = [node.value for node in inputs]
    self.incorporate(output, input_values)
    return output

  @override(VentureSP)
  def constrained_kernel(self, trace_handle, application_id, val):
    return SimulationConstrainedKernel(
      self, trace_handle, application_id, val)

  def simulate(self, _inputs, _prng):
    raise VentureBuiltinSPMethodError("Simulate not implemented!")

  def incorporate(self, output, inputs):
    pass

  def unincorporate(self, output, inputs):
    pass

class SimulationConstrainedKernel(ApplicationKernel):
  def __init__(self, sp, trace_handle, application_id, val):
    self.sp = sp
    self.trace_handle = trace_handle
    self.application_id = application_id
    self.val = val

  def extract(self, output, inputs):
    input_values = [node.value for node in inputs]
    self.sp.unincorporate(output, input_values)
    if output == self.val:
      weight = self.sp.logDensity(output, input_values)
    else:
      weight = float('-inf')
    return (weight, output)

  def regen(self, inputs):
    input_values = [node.value for node in inputs]
    output = self.val
    weight = self.sp.logDensity(output, input_values)
    self.sp.incorporate(output, input_values)
    return (weight, output)

  def restore(self, inputs, output):
    input_values = [node.value for node in inputs]
    self.sp.incorporate(output, input_values)
    return output


class RequestReferenceSP(VentureSP):
  def __init__(self):
    self.request_map = {}

  @override(VentureSP)
  def apply(self, trace_handle, application_id, inputs):
    assert application_id not in self.request_map
    raddr = self.request(trace_handle, application_id, inputs)
    self.request_map[application_id] = raddr
    return trace_handle.value_at(raddr)

  @override(VentureSP)
  def unapply(self, trace_handle, application_id, _output, _inputs):
    raddr = self.request_map.pop(application_id)
    trace_handle.free_request(raddr)
    return raddr

  @override(VentureSP)
  def restore(self, trace_handle, application_id, _inputs, raddr):
    trace_handle.restore_request(raddr)
    self.request_map[application_id] = raddr
    return trace_handle.value_at(raddr)

  def request(self, _trace_handle, _application_id, _inputs):
    raise VentureBuiltinSPMethodError("Request not implemented!")
