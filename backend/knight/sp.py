from typing import List
from typing import Tuple # Pylint doesn't understand type comments pylint: disable=unused-import
from typing import cast

from venture.lite.builtin import builtInSPs
from venture.lite.env import VentureEnvironment
from venture.lite.psp import NullRequestPSP
from venture.lite.sp_help import deterministic_typed
from venture.lite.sp_use import MockArgs
import venture.lite.sp as sp # pylint: disable=unused-import
import venture.lite.value as vv
import venture.lite.types as t
import venture.lite.inference_sps as inf
import venture.engine.inference # For effect on the inference sp registry

from venture.knight.types import App
from venture.knight.types import Datum
from venture.knight.types import Exp # pylint: disable=unused-import
from venture.knight.types import RegenResult # pylint: disable=unused-import
from venture.knight.types import Request
from venture.knight.types import Trace
from venture.knight.types import Var

class SP(vv.VentureValue):
  def regenerate(self, args, target, mechanism):
    # type: (List[vv.VentureValue], Trace, Trace) -> Tuple[float, RegenResult]
    raise NotImplementedError

  def regenerator_of(self):
    # type: () -> SP
    params = ["args", "target", "mechanism"]
    body = App([Var("regenerate"), Var("self"), Var("args"),
                Var("target"), Var("mechanism")])
    env = init_env()
    env.addBinding("self", self)
    return CompoundSP(params, body, env)

class CompoundSP(SP):
  def __init__(self, params, body, env):
    # type: (List[str], Exp, VentureEnvironment[vv.VentureValue]) -> None
    self.params = params
    self.body = body
    self.env = env

  def regenerate(self, args, target, mechanism):
    # type: (List[vv.VentureValue], Trace, Trace) -> Tuple[float, RegenResult]
    env = VentureEnvironment(self.env, self.params, args)
    req = Request(self.body, env, target, mechanism)
    return (0, req)

class SPFromLite(SP):
  def __init__(self, lite_sp):
    # type: (sp.SP) -> None
    self.lite_sp = lite_sp
    assert isinstance(lite_sp.requestPSP, NullRequestPSP)
    self.aux = lite_sp.constructSPAux()

  def regenerate(self, args, target, mechanism):
    # type: (List[vv.VentureValue], Trace, Trace) -> Tuple[float, RegenResult]
    assert isinstance(args, list)
    for a in args:
      assert isinstance(a, vv.VentureValue)
    if target.has():
      ans = target.get()
      score = self.lite_sp.outputPSP.logDensity(ans, MockArgs(args, self.aux))
    else:
      if mechanism.has():
        ans = mechanism.get()
      else:
        ans = self.lite_sp.outputPSP.simulate(MockArgs(args, self.aux))
      score = 0
    if self.lite_sp.outputPSP.isRandom():
      mechanism.set(ans)
    return (score, Datum(ans))

class GetCurrentTraceSP(SP):
  def regenerate(self, args, target, mechanism):
    # type: (List[vv.VentureValue], Trace, Trace) -> Tuple[float, RegenResult]
    return (0, Datum(mechanism))

class SubtraceSP(SP):
  def regenerate(self, args, target, mechanism):
    # type: (List[vv.VentureValue], Trace, Trace) -> Tuple[float, RegenResult]
    (trace, key) = args
    assert isinstance(trace, Trace)
    with trace.subtrace(key) as ans:
      ans.reify()
      return (0, Datum(ans))

class TraceHasSP(SP):
  def regenerate(self, args, target, mechanism):
    # type: (List[vv.VentureValue], Trace, Trace) -> Tuple[float, RegenResult]
    (trace,) = args
    assert isinstance(trace, Trace)
    return (0, Datum(vv.VentureBool(trace.has())))

class TraceGetSP(SP):
  def regenerate(self, args, target, mechanism):
    # type: (List[vv.VentureValue], Trace, Trace) -> Tuple[float, RegenResult]
    (trace,) = args
    assert isinstance(trace, Trace)
    return (0, Datum(trace.get()))

class TraceSetSP(SP):
  def regenerate(self, args, target, mechanism):
    # type: (List[vv.VentureValue], Trace, Trace) -> Tuple[float, RegenResult]
    (trace, val) = args
    assert isinstance(trace, Trace)
    trace.set(val)
    return (0, Datum(vv.VentureNil()))

class TraceClearSP(SP):
  def regenerate(self, args, target, mechanism):
    # type: (List[vv.VentureValue], Trace, Trace) -> Tuple[float, RegenResult]
    (trace,) = args
    assert isinstance(trace, Trace)
    trace.clear()
    return (0, Datum(vv.VentureNil()))

class TraceSitesSP(SP):
  def regenerate(self, args, target, mechanism):
    # type: (List[vv.VentureValue], Trace, Trace) -> Tuple[float, RegenResult]
    (trace,) = args
    assert isinstance(trace, Trace)
    return (0, Datum(vv.pythonListToVentureList(trace.sites())))

class RegenerateSP(SP):
  def regenerate(self, args, _target, _mechanism):
    # type: (List[vv.VentureValue], Trace, Trace) -> Tuple[float, RegenResult]
    (oper, subargs, target, mechanism) = args
    assert isinstance(oper, SP)
    assert isinstance(subargs, (vv.VenturePair, vv.VentureNil, vv.VentureArray, \
                                vv.VentureArrayUnboxed, vv.VentureSimplex))
    assert isinstance(target, Trace)
    assert isinstance(mechanism, Trace)
    # Pylint misunderstands typing.List
    # pylint: disable=unsubscriptable-object, invalid-sequence-index
    lst = cast(List[vv.VentureValue], subargs.asPythonList())
    for arg in lst:
      assert isinstance(arg, vv.VentureValue)
    from venture.knight.regen import r_apply
    (score, val) = r_apply(oper, lst, target, mechanism)
    return (0, Datum(vv.pythonListToVentureList([vv.VentureNumber(score), val])))

class MakeSPSP(SP):
  def regenerate(self, args, _target, _mechanism):
    # type: (List[vv.VentureValue], Trace, Trace) -> Tuple[float, RegenResult]
    (regenerator,) = args
    assert isinstance(regenerator, SP)
    return (0, Datum(MadeSP(regenerator)))

class MadeSP(SP):
  def __init__(self, regenerator_sp):
    # type: (SP) -> None
    self.regenerator_sp = regenerator_sp
  def regenerate(self, args, target, mechanism):
    # type: (List[vv.VentureValue], Trace, Trace) -> Tuple[float, RegenResult]
    new_args = [vv.pythonListToVentureList(args), target, mechanism]
    # XXX Should I invoke the trampoline here, on these fresh traces,
    # or propagate requests to my caller?
    from venture.knight.regen import r_apply
    (score, res) = r_apply(self.regenerator_sp, new_args, Trace(), Trace())
    (subscore, val) = res.asPythonList()
    assert isinstance(subscore, vv.VentureNumber), "%s is not a number" % (subscore,)
    # !? mypy doesn't understand asserts with error messages:
    # https://github.com/python/mypy/issues/2937
    assert isinstance(subscore, vv.VentureNumber)
    assert isinstance(val, vv.VentureValue) # Ban gradients' symbolic zeroes here.
    # XXX Is adding the right thing to do with these scores?
    return (score + subscore.getNumber(), Datum(val))
  def regenerator_of(self):
    # type: () -> SP
    return self.regenerator_sp

class RegeneratorOfSP(SP):
  def regenerate(self, args, target, mechanism):
    # type: (List[vv.VentureValue], Trace, Trace) -> Tuple[float, RegenResult]
    (sub_sp,) = args
    assert isinstance(sub_sp, SP)
    ans = sub_sp.regenerator_of()
    return (0, Datum(ans))

def make_global_env():
  # type: () -> VentureEnvironment[vv.VentureValue]
  env = VentureEnvironment() # type: VentureEnvironment[vv.VentureValue]
  for name, sp in builtInSPs().iteritems():
    if name not in ["lookup"]:
      if isinstance(sp.requestPSP, NullRequestPSP):
        env.addBinding(name, SPFromLite(sp))
  for name, sp in inf.inferenceSPsList:
    if isinstance(sp.requestPSP, NullRequestPSP):
      env.addBinding(name, SPFromLite(sp))
  env.addBinding("regenerate", RegenerateSP())
  env.addBinding("get_current_trace", GetCurrentTraceSP())
  env.addBinding("subtrace", SubtraceSP())
  env.addBinding("trace_has", TraceHasSP())
  env.addBinding("trace_get", TraceGetSP())
  env.addBinding("trace_set", TraceSetSP())
  env.addBinding("trace_clear", TraceClearSP())
  env.addBinding("trace_sites", TraceSitesSP())
  env.addBinding("sp", MakeSPSP())
  env.addBinding("regenerator_of", RegeneratorOfSP())
  lite_and_sp = deterministic_typed(lambda a, b: a and b,
      [t.Bool, t.Bool], t.Bool,
      descr="non-short-circuiting and")
  env.addBinding("and", SPFromLite(lite_and_sp))
  lite_or_sp = deterministic_typed(lambda a, b: a or b,
      [t.Bool, t.Bool], t.Bool,
      descr="non-short-circuiting or")
  env.addBinding("or", SPFromLite(lite_or_sp))
  # venture.lite.types.HomogeneousMappingType is not extensible to
  # include traces, but I want lookup to accept them.  Change the type
  # declaration.
  updated_lookup_sp = deterministic_typed(lambda xs, x: xs.lookup(x),
      [t.AnyType("<mapping l v>"), t.AnyType("k")],
      t.AnyType("v"))
  env.addBinding("lookup", SPFromLite(updated_lookup_sp))
  return env

the_global_env = make_global_env()

def init_env():
  # type: () -> VentureEnvironment[vv.VentureValue]
  return VentureEnvironment(the_global_env)
