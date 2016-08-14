from venture.lite.env import VentureEnvironment
import venture.lite.types as t

from venture.mite.sp import SimulationSP
from venture.mite.sp_registry import registerBuiltinSP

class ExtendEnvSP(SimulationSP):
  def simulate(self, inputs, _prng):
    assert len(inputs) == 3
    env = inputs[0]
    sym = t.Symbol.asPython(inputs[1])
    node = t.Blob.asPython(inputs[2])
    return VentureEnvironment(env, [sym], [node])

registerBuiltinSP("extend_environment", ExtendEnvSP())
