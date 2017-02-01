from typing import Callable
from typing import List
from typing import NamedTuple
from typing import Tuple
from typing import Union

import venture.lite.value as vv 
from venture.lite.env import VentureEnvironment

from venture.knight.types import Exp
from venture.knight.types import App
from venture.knight.types import Lit
from venture.knight.types import Var
from venture.knight.types import Lam
from venture.knight.types import Trace
from venture.knight.types import Datum
from venture.knight.types import Request
from venture.knight.sp import SP
from venture.knight.sp import CompoundSP

def regen(exp, env, constraints, interventions):
  # type: (Exp, VentureEnvironment[vv.VentureValue], Trace, Trace) -> Tuple[float, vv.VentureValue]
  if interventions.has():
    return (0, interventions.get())
  else:
    return do_regen(exp, env, constraints, interventions)

def do_regen(exp, env, constraints, interventions):
  # type: (Exp, VentureEnvironment[vv.VentureValue], Trace, Trace) -> Tuple[float, vv.VentureValue]
  if isinstance(exp, App):
    (sub_score, subvals) = regen_list(exp.subs, env, constraints, interventions)
    oper = subvals[0]
    assert isinstance(oper, SP)
    (app_score, val) = r_apply(oper, subvals[1:],
                               constraints.application_subtrace(),
                               interventions.application_subtrace())
    return (sub_score + app_score, val)
  if isinstance(exp, Lit):
    return (0, exp.val)
  if isinstance(exp, Var):
    return (0, env.findSymbol(exp.name))
  if isinstance(exp, Lam):
    return (0, CompoundSP(exp.params, exp.body, env))

def regen_list(exps, env, constraints, interventions):
  # type: (List[Exp], VentureEnvironment[vv.VentureValue], Trace, Trace) -> Tuple[float, List[vv.VentureValue]]
  # This is mapM (\e -> regen(e, env, trace)) in the Writer (Sum Double) monad.
  score = 0.0
  anss = []
  for (i, e) in enumerate(exps):
    (dscore, ans) = regen(e, env, constraints.subexpr_subtrace(i),
                          interventions.subexpr_subtrace(i))
    score += dscore
    anss.append(ans)
  return (score, anss)

def r_apply(oper, args, constraints, interventions):
  # type: (SP, List[vv.VentureValue], Trace, Trace) -> Tuple[float, vv.VentureValue]
  if interventions.has():
    return (0, interventions.get())
  else:
    return do_r_apply(oper, args, constraints, interventions)

def do_r_apply(oper, args, constraints, interventions):
  # type: (SP, List[vv.VentureValue], Trace, Trace) -> Tuple[float, vv.VentureValue]
  (app_score, res) = oper.regenerate(args, constraints, interventions)
  if isinstance(res, Datum):
    return (app_score, res.datum)
  elif isinstance(res, Request):
    (recur_score, val) = regen(res.exp, res.env, res.constraints, res.interventions)
    return (app_score + recur_score, val)
