from typing import Callable
from typing import Tuple

import venture.lite.value as vv 

from venture.knight.types import RegenResult
from venture.knight.types import Trace

class SP(vv.VentureValue):
  def regenerator(self):
    # type: () -> Callable[[List[vv.VentureValue], Trace], Tuple[float, RegenResult]]
    raise NotImplementedError

class CompoundSP(SP): pass
