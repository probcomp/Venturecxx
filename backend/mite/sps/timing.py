import time

import venture.lite.types as t

from venture.mite.sp import SimulationSP
from venture.mite.sp_registry import registerBuiltinSP

class TimeSP(SimulationSP):
  def simulate(self, inputs, _prng):
    assert len(inputs) == 0
    return t.Number.asVentureValue(time.time())

registerBuiltinSP("time", TimeSP())
