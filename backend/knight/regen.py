from typing import cast
from typing import List # Pylint doesn't understand type comments pylint: disable=unused-import
from typing import Tuple # pylint: disable=unused-import

from venture.lite.env import VentureEnvironment # pylint: disable=unused-import
import venture.lite.value as vv

from venture.knight.sp import CompoundSP
from venture.knight.sp import SP
from venture.knight.types import App
from venture.knight.types import Datum
from venture.knight.types import Def
from venture.knight.types import Exp # pylint: disable=unused-import
from venture.knight.types import Lam
from venture.knight.types import Lit
from venture.knight.types import Request
from venture.knight.types import Seq
from venture.knight.types import Spl
from venture.knight.types import Trace # pylint: disable=unused-import
from venture.knight.types import Var

def regen(exp, env, target, mechanism):
  # type: (Exp, VentureEnvironment[vv.VentureValue], Trace, Trace) -> Tuple[float, vv.VentureValue]
  desired_val = None
  if mechanism.has():
    desired_val = mechanism.get()
  (score, val) = do_regen(exp, env, target, mechanism)
  if desired_val is not None:
    val = desired_val
    if mechanism.has():
      mechanism.set(desired_val)
  return (score, val)

def do_regen(exp, env, target, mechanism):
  # type: (Exp, VentureEnvironment[vv.VentureValue], Trace, Trace) -> Tuple[float, vv.VentureValue]
  if isinstance(exp, App):
    (sub_score, subvals) = regen_list(exp.subs, env, target, mechanism)
    oper = subvals[0]
    assert isinstance(oper, SP)
    with target.application_subtrace() as c2:
      with mechanism.application_subtrace() as i2:
        (app_score, val) = r_apply(oper, subvals[1:], c2, i2)
        return (sub_score + app_score, val)
  if isinstance(exp, Lit):
    return (0, exp.val)
  if isinstance(exp, Var):
    return (0, env.findSymbol(exp.name))
  if isinstance(exp, Lam):
    return (0, CompoundSP(exp.params, exp.body, env))
  if isinstance(exp, Seq):
    # This can also be emulated by applying a procedure that returns
    # the last argument (since the language is strict).
    (sub_score, subvals) = regen_list(exp.subs, env, target, mechanism)
    if len(exp.subs) > 0:
      return (sub_score, subvals[-1])
    else:
      return (sub_score, vv.VentureNil())
  if isinstance(exp, Def):
    with target.definition_subtrace() as t2:
      with mechanism.definition_subtrace() as m2:
        (sub_score, subval) = regen(exp.expr, env, t2, m2)
        match_bind(exp.pat, subval, env)
        return (sub_score, vv.VentureNil())
  assert False, "Unknown expression type %s" % (exp,)

def regen_list(exps, env, target, mechanism):
  # type: (List[Exp], VentureEnvironment[vv.VentureValue], Trace, Trace) -> Tuple[float, List[vv.VentureValue]]
  # This is mapM (\e -> regen(e, env, trace)) in the Writer (Sum Double) monad,
  # except for handling splice expressions
  score = 0.0
  anss = [] # type: List[vv.VentureValue]
  for (i, e) in enumerate(exps):
    with target.subexpr_subtrace(i) as c2:
      with mechanism.subexpr_subtrace(i) as i2:
        if isinstance(e, Spl):
          (dscore, ans) = regen(e.sub, env, c2, i2)
          score += dscore
          anss += cast(List[vv.VentureValue], ans.asPythonList())
        else:
          (dscore, ans) = regen(e, env, c2, i2)
          score += dscore
          anss.append(ans)
  return (score, anss)

def match_bind(pat, val, env):
  # type: (Exp, vv.VentureValue, VentureEnvironment[vv.VentureValue]) -> None
  if isinstance(pat, Var):
    if pat.name != '_':
      env.addBinding(pat.name, val)
  elif isinstance(pat, Seq):
    if isinstance(val, Trace):
      keys = sorted(val.sites())
      vals = [val.get_at(k) for k in keys]
    else:
      vals = val.asPythonList()
    for (p, v) in zip(pat.subs, vals):
      match_bind(p, v, env)
  else:
    raise Exception("Invalid binding expression %s", pat)

def r_apply(oper, args, target, mechanism):
  # type: (SP, List[vv.VentureValue], Trace, Trace) -> Tuple[float, vv.VentureValue]
  desired_val = None
  if mechanism.has():
    desired_val = mechanism.get()
  (score, val) = do_r_apply(oper, args, target, mechanism)
  if desired_val is not None:
    val = desired_val
    if mechanism.has():
      mechanism.set(desired_val)
  return (score, val)

def do_r_apply(oper, args, target, mechanism):
  # type: (SP, List[vv.VentureValue], Trace, Trace) -> Tuple[float, vv.VentureValue]
  (app_score, res) = oper.regenerate(args, target, mechanism)
  if isinstance(res, Datum):
    return (app_score, res.datum)
  elif isinstance(res, Request):
    (recur_score, val) = regen(res.exp, res.env, res.target, res.mechanism)
    return (app_score + recur_score, val)
