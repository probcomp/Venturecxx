import copy

from venture.lite.builtin import builtInSPs
from venture.lite.exception import VentureError
from venture.lite.psp import NullRequestPSP
from venture.lite.sp import VentureSPRecord

from venture.mite.sp_registry import registerBuiltinSP
from venture.mite.sp import SimulationSP

class LiteSP(SimulationSP):
  def __init__(self, wrapped_sp, wrapped_aux=None):
    self.wrapped_sp = wrapped_sp
    self.wrapped_aux = wrapped_aux
    assert isinstance(self.wrapped_sp.requestPSP, NullRequestPSP), \
      "Cannot wrap requesting SPs"

  def wrap_args(self, args):
    # TODO: use one of Alexey's new Args classes
    args = copy.copy(args)
    args.spaux = lambda: self.wrapped_aux
    return args

  def simulate(self, args):
    result = self.wrapped_sp.outputPSP.simulate(self.wrap_args(args))
    if isinstance(result, VentureSPRecord):
      result = LiteSP(result.sp, result.spAux)
    return result

  def logDensity(self, value, args):
    return self.wrapped_sp.outputPSP.logDensity(value, self.wrap_args(args))

  def incorporate(self, value, args):
    return self.wrapped_sp.outputPSP.incorporate(value, self.wrap_args(args))

  def unincorporate(self, value, args):
    return self.wrapped_sp.outputPSP.unincorporate(value, self.wrap_args(args))

  def constrain(self, value, args):
    if self.wrapped_sp.outputPSP.isRandom():
      return super(LiteSP, self).constrain(value, args)
    else:
      raise VentureError("Cannot constrain a deterministic value.")

for name, sp in builtInSPs().iteritems():
  if isinstance(sp.requestPSP, NullRequestPSP):
    registerBuiltinSP(name, LiteSP(sp))

