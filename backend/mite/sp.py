from venture.lite.address import emptyAddress
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
    ref = self.request(args)
    self.request_map[args.node] = ref
    return args.trace.valueAt(ref)

  @override(VentureSP)
  def unapply(self, args):
    ref = self.request_map.pop(args.node)
    args.freeRequest(ref)

  @override(VentureSP)
  def constrain(self, value, args):
    ref = self.request_map[args.node]
    weight = args.constrain(ref, value)
    return weight

  def request(self, _args):
    raise VentureBuiltinSPMethodError("Request not implemented!")

class Args(LiteArgs):
  def outputValue(self):
    return self.trace.valueAt(self.node)

  def newRequest(self, exp, env, addr=emptyAddress):
    return self.trace.newRequest(self.node, addr, exp, env)

  def shareRequest(self, ref):
    return self.trace.shareRequest(self.node, ref)

  def freeRequest(self, ref):
    return self.trace.freeRequest(self.node, ref)

  def constrain(self, ref, value):
    return self.trace.constrainRequest(self.node, ref, value)
