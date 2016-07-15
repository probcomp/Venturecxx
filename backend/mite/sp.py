from venture.lite.exception import VentureBuiltinSPMethodError
from venture.lite.node import TraceNodeArgs as LiteTraceNodeArgs
from venture.lite.utils import override
from venture.lite.value import VentureValue, VentureNil
import venture.value.dicts as v

class VentureSP(VentureValue):
  """A stochastic procedure."""

  def apply(self, _application_id, _args):
    raise VentureBuiltinSPMethodError("Apply not implemented!")

  def unapply(self, _application_id, _output, _args):
    raise VentureBuiltinSPMethodError("Cannot unapply")

  def restore(self, _application_id, _args, _trace_fragment):
    raise VentureBuiltinSPMethodError("Cannot restore previous state")

  def logDensity(self, _value, _args):
    raise VentureBuiltinSPMethodError("Cannot assess log density")

  def show(self):
    return "<procedure>"

  def extractStateAsVentureValue(self):
    return VentureNil()

  def asStackDict(self, _trace=None):
    return v.sp(self.show(), self.extractStateAsVentureValue().asStackDict())

class SimulationSP(VentureSP):
  @override(VentureSP)
  def apply(self, _application_id, args):
    value = self.simulate(args)
    self.incorporate(value, args)
    return value

  @override(VentureSP)
  def unapply(self, _application_id, output, args):
    self.unincorporate(output, args)
    return output

  @override(VentureSP)
  def restore(self, _application_id, args, value):
    self.incorporate(value, args)
    return value

  def simulate(self, _args):
    raise VentureBuiltinSPMethodError("Simulate not implemented!")

  def incorporate(self, value, args):
    pass

  def unincorporate(self, value, args):
    pass

class RequestReferenceSP(VentureSP):
  def __init__(self):
    self.request_map = {}

  @override(VentureSP)
  def apply(self, application_id, args):
    assert application_id not in self.request_map
    raddr = self.request(application_id, args)
    self.request_map[application_id] = raddr
    return args.requestedValue(raddr)

  @override(VentureSP)
  def unapply(self, application_id, _output, args):
    raddr = self.request_map.pop(application_id)
    args.decRequest(raddr)
    return None

  @override(VentureSP)
  def restore(self, application_id, args, _trace_fragment):
    # NB: this assumes that the request made is deterministic
    # so we can just reapply
    return self.apply(application_id, args)

  def request(self, _application_id, _args):
    raise VentureBuiltinSPMethodError("Request not implemented!")
