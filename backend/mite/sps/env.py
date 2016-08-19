from venture.lite.env import VentureEnvironment
import venture.lite.types as t

from venture.mite.sp import VentureSP, SimulationSP
from venture.mite.sp_registry import registerBuiltinSP

class ExtendEnvSP(SimulationSP):
  def simulate(self, inputs, _prng):
    assert len(inputs) == 3
    env = inputs[0]
    sym = t.Symbol.asPython(inputs[1])
    node = t.Blob.asPython(inputs[2])
    return VentureEnvironment(env, [sym], [node])

registerBuiltinSP("extend_environment", ExtendEnvSP())

# TODO this is stubbed
class GetCurrentEnvironmentSP(VentureSP):
  def apply(self, trace_handle, _application_id, inputs):
    return trace_handle.trace.global_env

registerBuiltinSP("get_current_environment", GetCurrentEnvironmentSP())
