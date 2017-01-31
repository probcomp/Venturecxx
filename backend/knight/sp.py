from typing import Callable
from typing import Tuple
from typing import List
from typing import cast

import venture.lite.value as vv 
from venture.lite.builtin import builtInSPs
from venture.lite.env import VentureEnvironment
import venture.lite.sp as sp
from venture.lite.sp_use import MockArgs
from venture.lite.psp import NullRequestPSP

from venture.knight.types import Datum
from venture.knight.types import Exp
from venture.knight.types import RegenResult
from venture.knight.types import Request
from venture.knight.types import Trace

class SP(vv.VentureValue):
  def regenerate(self, args, constraints, interventions):
    # type: (List[vv.VentureValue], Trace, Trace) -> Tuple[float, RegenResult]
    raise NotImplementedError

class CompoundSP(SP):
  def __init__(self, params, body, env):
    # type: (List[str], Exp, VentureEnvironment[vv.VentureValue]) -> None
    self.params = params
    self.body = body
    self.env = env

  def regenerate(self, args, constraints, interventions):
    # type: (List[vv.VentureValue], Trace, Trace) -> Tuple[float, RegenResult]
    env = VentureEnvironment(self.env, self.params, args)
    req = Request(self.body, env, constraints, interventions)
    return (0, req)

class SPFromLite(SP):
  def __init__(self, lite_sp):
    # type: (sp.SP) -> None
    self.lite_sp = lite_sp
    assert isinstance(lite_sp.requestPSP, NullRequestPSP)
    self.aux = lite_sp.constructSPAux()

  def regenerate(self, args, constraints, interventions):
    # type: (List[vv.VentureValue], Trace, Trace) -> Tuple[float, RegenResult]
    if constraints.has():
      v = constraints.get()
      w = self.lite_sp.outputPSP.logDensity(v, MockArgs(args, self.aux))
      return (w, Datum(v))
    else:
      ans = self.lite_sp.outputPSP.simulate(MockArgs(args, self.aux))
      return (0, Datum(ans))

class RegenerateSP(SP):
  def regenerate(self, args, _constraints, _interventions):
    # type: (List[vv.VentureValue], Trace, Trace) -> Tuple[float, RegenResult]
    (oper, subargs, constraints, interventions) = args
    assert isinstance(oper, SP)
    assert isinstance(subargs, (vv.VenturePair, vv.VentureNil, vv.VentureArray, \
                                vv.VentureArrayUnboxed, vv.VentureSimplex))
    assert isinstance(constraints, Trace)
    assert isinstance(interventions, Trace)
    # Pylint misunderstands typing.List
    # pylint: disable=unsubscriptable-object, invalid-sequence-index
    lst = cast(List[vv.VentureValue], subargs.asPythonList())
    for arg in lst:
      assert isinstance(arg, vv.VentureValue)
    from venture.knight.regen import r_apply
    (w, val) = r_apply(oper, lst, constraints, interventions)
    return (w, Datum(vv.VenturePair((vv.VentureNumber(w), val))))

def init_env():
  # type: () -> VentureEnvironment[vv.VentureValue]
  env = VentureEnvironment() # type: VentureEnvironment[vv.VentureValue]
  for name, sp in builtInSPs().iteritems():
    if isinstance(sp.requestPSP, NullRequestPSP):
      env.addBinding(name, SPFromLite(sp))
  env.addBinding("regenerate", RegenerateSP())
  return VentureEnvironment(env)
