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
from venture.knight.types import App
from venture.knight.types import Var
from venture.knight.types import RegenResult
from venture.knight.types import Request
from venture.knight.types import Trace

class SP(vv.VentureValue):
  def regenerate(self, args, constraints, interventions):
    # type: (List[vv.VentureValue], Trace, Trace) -> Tuple[float, RegenResult]
    raise NotImplementedError

  def regenerator_of(self):
    # type: () -> SP
    params = ["args", "constraints", "interventions"]
    body = App([Var("regenerate"), Var("self"), Var("args"),
                Var("constraints"), Var("interventions")])
    env = init_env()
    env.addBinding("self", self)
    return CompoundSP(params, body, env)

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
      score = self.lite_sp.outputPSP.logDensity(ans, MockArgs(args, self.aux))
    else:
      ans = self.lite_sp.outputPSP.simulate(MockArgs(args, self.aux))
      score = 0
    interventions.set(ans)
    return (score, Datum(ans))

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
    (trace,) = args
    assert isinstance(trace, Trace)
    return (0, Datum(vv.VentureBool(trace.has())))

class TraceGetSP(SP):
  def regenerate(self, args, constraints, interventions):
    # type: (List[vv.VentureValue], Trace, Trace) -> Tuple[float, RegenResult]
    (trace,) = args
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
    (score, val) = r_apply(oper, lst, constraints, interventions)
    return (0, Datum(vv.VenturePair((vv.VentureNumber(score), val))))

class MakeSPSP(SP):
  def regenerate(self, args, _constraints, _interventions):
    # type: (List[vv.VentureValue], Trace, Trace) -> Tuple[float, RegenResult]
    (regenerator,) = args
    assert isinstance(regenerator, SP)
    return (0, Datum(MadeSP(regenerator)))

class MadeSP(SP):
  def __init__(self, regenerator_sp):
    # type: (SP) -> None
    self.regenerator_sp = regenerator_sp
  def regenerate(self, args, constraints, interventions):
    # type: (List[vv.VentureValue], Trace, Trace) -> Tuple[float, RegenResult]
    new_args = [vv.pythonListToVentureList(args), constraints, interventions]
    # XXX Should I invoke the trampoline here, on these fresh traces,
    # or propagate requests to my caller?
    from venture.knight.regen import r_apply
    (score, res) = r_apply(self.regenerator_sp, new_args, Trace(), Trace())
    assert isinstance(res, vv.VenturePair)
    subscore = res.first
    assert isinstance(subscore, vv.VentureNumber)
    val = res.rest
    assert isinstance(val, vv.VentureValue) # Ban gradients' symbolic zeroes here.
    # XXX Is adding the right thing to do with these scores?
    return (score + subscore.getNumber(), Datum(val))

class RegeneratorOfSP(SP):
  def regenerate(self, args, constraints, interventions):
    # type: (List[vv.VentureValue], Trace, Trace) -> Tuple[float, RegenResult]
    (sub_sp,) = args
    assert isinstance(sub_sp, SP)
    ans = sub_sp.regenerator_of()
    return (0, Datum(ans))

def make_global_env():
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
  env.addBinding("sp", MakeSPSP())
  env.addBinding("regenerator_of", RegeneratorOfSP())
  return env

the_global_env = make_global_env()

def init_env():
  # type: () -> VentureEnvironment[vv.VentureValue]
  return VentureEnvironment(the_global_env)
