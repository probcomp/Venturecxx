from typing import Callable
from typing import Tuple

import venture.lite.value as vv 
from venture.lite.env import VentureEnvironment

from venture.knight.types import Exp
from venture.knight.types import RegenResult
from venture.knight.types import Request
from venture.knight.types import Trace

class SP(vv.VentureValue):
  def regenerate(self, args, trace):
    # type: (List[vv.VentureValue], Trace) -> Tuple[float, RegenResult]
    raise NotImplementedError

class CompoundSP(SP):
  def __init__(self, params, body, env):
    # type: (List[str], Exp, VentureEnvironment[vv.VentureValue]) -> None
    self.params = params
    self.body = body
    self.env = env

  def regenerate(self, args, trace):
    env = VentureEnvironment(self.env, self.params, args)
    req = Request(self.body, env, trace)
    return (0, req)
