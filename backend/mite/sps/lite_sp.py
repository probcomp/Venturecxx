import copy

from venture.lite.builtin import builtInSPs
from venture.lite.exception import VentureError
from venture.lite.psp import NullRequestPSP
from venture.lite.sp import VentureSPRecord
from venture.lite.sp_use import MockArgs

from venture.mite.sp_registry import registerBuiltinSP
from venture.mite.sp import SimulationSP

class LiteSP(SimulationSP):
  def __init__(self, wrapped_sp, wrapped_aux=None):
    self.wrapped_sp = wrapped_sp
    self.wrapped_aux = wrapped_aux
    assert isinstance(self.wrapped_sp.requestPSP, NullRequestPSP), \
      "Cannot wrap requesting SPs"

  def wrap_args(self, inputs, prng=None):
    # TODO: use one of Alexey's new Args classes
    if prng is not None:
      return MockArgs(inputs, self.wrapped_aux,
                      prng.py_prng, prng.np_prng)
    else:
      return MockArgs(inputs, self.wrapped_aux)

  def simulate(self, inputs, prng):
    result = self.wrapped_sp.outputPSP.simulate(self.wrap_args(inputs, prng))
    if isinstance(result, VentureSPRecord):
      result = LiteSP(result.sp, result.spAux)
    return result

  def logDensity(self, output, inputs):
    return self.wrapped_sp.outputPSP.logDensity(output, self.wrap_args(inputs))

  def incorporate(self, output, inputs):
    return self.wrapped_sp.outputPSP.incorporate(output, self.wrap_args(inputs))

  def unincorporate(self, output, inputs):
    return self.wrapped_sp.outputPSP.unincorporate(output, self.wrap_args(inputs))

for name, sp in builtInSPs().iteritems():
  if isinstance(sp.requestPSP, NullRequestPSP):
    registerBuiltinSP(name, LiteSP(sp))

