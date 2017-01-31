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
      ans = constraints.get()
      w = self.lite_sp.outputPSP.logDensity(ans, MockArgs(args, self.aux))
    else:
      ans = self.lite_sp.outputPSP.simulate(MockArgs(args, self.aux))
      w = 0
    interventions.set(ans)
    return (w, Datum(ans))

class GetCurrentTraceSP(SP):
  def regenerate(self, args, constraints, interventions):
    # type: (List[vv.VentureValue], Trace, Trace) -> Tuple[float, RegenResult]
    return (0, Datum(interventions))

class SubtraceSP(SP):
  def regenerate(self, args, constraints, interventions):
    # type: (List[vv.VentureValue], Trace, Trace) -> Tuple[float, RegenResult]
    (trace, key) = args
    assert isinstance(trace, Trace)
    ans = trace.subtrace(key)
    return (0, Datum(ans))

class TraceHasSP(SP):
  def regenerate(self, args, constraints, interventions):
    # type: (List[vv.VentureValue], Trace, Trace) -> Tuple[float, RegenResult]
    (trace) = args
    assert isinstance(trace, Trace)
    return (0, Datum(vv.VentureBool(trace.has())))

class TraceGetSP(SP):
  def regenerate(self, args, constraints, interventions):
    # type: (List[vv.VentureValue], Trace, Trace) -> Tuple[float, RegenResult]
    (trace) = args
    assert isinstance(trace, Trace)
    return (0, Datum(trace.get()))

class TraceSetSP(SP):
  def regenerate(self, args, constraints, interventions):
    # type: (List[vv.VentureValue], Trace, Trace) -> Tuple[float, RegenResult]
    (trace, val) = args
    assert isinstance(trace, Trace)
    trace.set(val)
    return (0, Datum(vv.VentureNil()))

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
  env.addBinding("get_current_trace", GetCurrentTraceSP())
  env.addBinding("subtrace", SubtraceSP())
  env.addBinding("trace_has", TraceHasSP())
  env.addBinding("trace_get", TraceGetSP())
  env.addBinding("trace_set", TraceSetSP())
  return VentureEnvironment(env)
