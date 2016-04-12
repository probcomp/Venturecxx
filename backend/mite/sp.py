from venture.lite.exception import VentureBuiltinSPMethodError
from venture.lite.node import Args as LiteArgs
from venture.lite.utils import override
from venture.lite.value import VentureValue
import venture.value.dicts as v

class VentureSP(VentureValue):
  """A stochastic procedure."""

  def apply(self, _args):
    raise VentureBuiltinSPMethodError("Apply not implemented!")

  def unapply(self, _args):
    raise VentureBuiltinSPMethodError("Unapply not implemented!")

  def logDensity(self, _value, _args):
    raise VentureBuiltinSPMethodError("Cannot assess log density")

  def constrain(self, _value, _args):
    raise VentureBuiltinSPMethodError("Cannot constrain")

  def unconstrain(self, _args):
    raise VentureBuiltinSPMethodError("Cannot unconstrain")

  def show(self):
    return "<procedure>"

  def asStackDict(self, _trace=None):
    return v.sp(self.show())

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

  @override(VentureSP)
  def constrain(self, value, args):
    self.unapply(args)
    weight = self.logDensity(value, args)
    self.incorporate(value, args)
    return weight

  @override(VentureSP)
  def unconstrain(self, args):
    value = args.outputValue()
    self.unincorporate(value, args)
    weight = self.logDensity(value, args)
    return weight, self.apply(args)

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

  @override(VentureSP)
  def constrain(self, value, args):
    raddr = self.request_map[args.node]
    weight = args.constrain(raddr, value)
    return weight

  def request(self, _args):
    raise VentureBuiltinSPMethodError("Request not implemented!")

class Args(LiteArgs):
  def outputValue(self):
    return self.trace.valueAt(self.node)

  def operandValue(self, ix):
    return self.trace.valueAt(self.operandNodes[ix])

  def newRequest(self, raddr, exp, env):
    return self.trace.newRequest(self.node, raddr, exp, env)

  def incRequest(self, raddr):
    return self.trace.incRequest(self.node, raddr)

  def decRequest(self, raddr):
    return self.trace.decRequest(self.node, raddr)

  def hasRequest(self, raddr):
    return self.trace.hasRequestAt(self.node, raddr)

  def requestedValue(self, raddr):
    return self.trace.requestedValueAt(self.node, raddr)

  def constrain(self, raddr, value):
    return self.trace.constrainRequest(self.node, raddr, value)
