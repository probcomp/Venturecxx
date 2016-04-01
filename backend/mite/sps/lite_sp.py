from venture.lite.builtin import builtInSPs
from venture.lite.psp import NullRequestPSP

from venture.mite.sp_registry import registerBuiltinSP
from venture.mite.sp import SimulationSP

class LiteSP(SimulationSP):
  def __init__(self, wrapped_sp):
    self.wrapped_sp = wrapped_sp
    assert isinstance(self.wrapped_sp.requestPSP, NullRequestPSP), \
      "Cannot wrap requesting SPs"

  def simulate(self, args):
    return self.wrapped_sp.outputPSP.simulate(args)

  def incorporate(self, value, args):
    return self.wrapped_sp.outputPSP.incorporate(value, args)

  def unincorporate(self, value, args):
    return self.wrapped_sp.outputPSP.unincorporate(value, args)

for name, sp in builtInSPs().iteritems():
  if isinstance(sp.requestPSP, NullRequestPSP):
    registerBuiltinSP(name, LiteSP(sp))

