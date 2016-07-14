from venture.lite.exception import VentureBuiltinSPMethodError
from venture.lite.node import TraceNodeArgs as LiteTraceNodeArgs
from venture.lite.utils import override
from venture.lite.value import VentureValue, VentureNil
import venture.value.dicts as v

class VentureSP(VentureValue):
  """A stochastic procedure."""

  def apply(self, _args):
    raise VentureBuiltinSPMethodError("Apply not implemented!")

  def unapply(self, _args):
    raise VentureBuiltinSPMethodError("Cannot unapply")

  def restore(self, _args, _trace_fragment):
    raise VentureBuiltinSPMethodError("Cannot restore previous state")

  def logDensity(self, _value, _args):
    raise VentureBuiltinSPMethodError("Cannot assess log density")

  # TODO: replace this trio of methods with constrained kernels.

  def constrain(self, _value, _args):
    raise VentureBuiltinSPMethodError("Cannot constrain")

  def unconstrain(self, _args):
    raise VentureBuiltinSPMethodError("Cannot unconstrain")

  def reconstrain(self, _value, _args):
    raise VentureBuiltinSPMethodError("Cannot unconstrain")

  def show(self):
    return "<procedure>"

  def extractStateAsVentureValue(self):
    return VentureNil()

  def asStackDict(self, _trace=None):
    return v.sp(self.show(), self.extractStateAsVentureValue().asStackDict())

class SimulationSP(VentureSP):
  @override(VentureSP)
  def apply(self, args):
    value = self.simulate(args)
    self.incorporate(value, args)
    return value

  @override(VentureSP)
  def unapply(self, args):
    value = args.outputValue()
    self.unincorporate(value, args)
    return value

  @override(VentureSP)
  def restore(self, args, value):
    self.incorporate(value, args)
    return value

  @override(VentureSP)
  def constrain(self, value, args):
    oldValue = args.outputValue()
    self.unincorporate(oldValue, args)
    weight = self.logDensity(value, args)
    self.incorporate(value, args)
    return weight

  @override(VentureSP)
  def unconstrain(self, args):
    value = args.outputValue()
    self.unincorporate(value, args)
    weight = self.logDensity(value, args)
    newValue = self.simulate(args)
    self.incorporate(newValue, args)
    return weight, newValue

  @override(VentureSP)
  def reconstrain(self, value, args):
    return self.constrain(value, args)

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
  def apply(self, args):
    assert args.node not in self.request_map
    raddr = self.request(args)
    self.request_map[args.node] = raddr
    return args.requestedValue(raddr)

  @override(VentureSP)
  def unapply(self, args):
    raddr = self.request_map.pop(args.node)
    args.decRequest(raddr)
    return None

  @override(VentureSP)
  def restore(self, args, _trace_fragment):
    # NB: this assumes that the request made is deterministic
    # so we can just reapply
    return self.apply(args)

  @override(VentureSP)
  def constrain(self, value, args):
    raddr = self.request_map[args.node]
    weight = args.constrain(raddr, value)
    return weight

  @override(VentureSP)
  def unconstrain(self, args):
    raddr = self.request_map[args.node]
    weight = args.unconstrain(raddr)
    return weight, args.requestedValue(raddr)

  @override(VentureSP)
  def reconstrain(self, value, args):
    return self.constrain(value, args)

  def request(self, _args):
    raise VentureBuiltinSPMethodError("Request not implemented!")
