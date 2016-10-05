from venture.lite.builtin import builtInSPs
from venture.lite.psp import NullRequestPSP
from venture.lite.sp import VentureSPRecord
from venture.lite.sp_use import MockArgs

from venture.mite.sp import SimulationSP
from venture.mite.sp_registry import registerBuiltinSP

class LiteSP(SimulationSP):
  def __init__(self, wrapped_sp, wrapped_aux=None):
    self.wrapped_sp = wrapped_sp
    self.wrapped_aux = wrapped_aux
    assert isinstance(self.wrapped_sp.requestPSP, NullRequestPSP), \
      "Cannot wrap requesting SP %s of type %s" % \
      (wrapped_sp.requestPSP.description(None), type(wrapped_sp.requestPSP))

  def wrap_args(self, inputs, prng=None):
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

  def log_density(self, output, inputs):
    return self.wrapped_sp.outputPSP.logDensity(output, self.wrap_args(inputs))

  def incorporate(self, output, inputs):
    return self.wrapped_sp.outputPSP.incorporate(output, self.wrap_args(inputs))

  def unincorporate(self, output, inputs):
    return self.wrapped_sp.outputPSP.unincorporate(output, self.wrap_args(inputs))

  def log_density_bound(self, output, inputs):
    return self.wrapped_sp.outputPSP.logDensityBound(output, self.wrap_args(inputs))

  def run_in_helper_trace(self, method, inputs):
    # XXX This name is chosen to agree with MadeSimulationSP and
    # MadeFullSP, which is relevant because it is invoked directly
    # from traces.py instead of going through the Python method
    # interface.
    # XXX The signature of simulate is different, b/c of the prng and
    # the absence of the 'output' argument.
    return getattr(self, method)(inputs[0], inputs[1:])

for name, sp in builtInSPs().iteritems():
  if isinstance(sp.requestPSP, NullRequestPSP):
    registerBuiltinSP(name, LiteSP(sp))

