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

def regen(exp, env, trace):
  # type: (Exp, VentureEnvironment[vv.VentureValue], Trace) -> Tuple[float, vv.VentureValue]
  if isinstance(exp, App):
    (subw, subvals) = regen_list(exp.subs, env, trace)
    oper = subvals[0]
    assert isinstance(oper, SP)
    (appw, val) = r_apply(oper, subvals[1:], trace.application_subtrace())
    return (subw + appw, val)
  if isinstance(exp, Lit):
    return (0, exp.val)
  if isinstance(exp, Var):
    return (0, env.findSymbol(exp.name))

def regen_list(exps, env, trace):
  # type: (List[Exp], VentureEnvironment[vv.VentureValue], Trace) -> Tuple[float, List[vv.VentureValue]]
  # This is mapM (\e -> regen(e, env, trace)) in the Writer (Sum Double) monad.
  w = 0.0
  anss = []
  for (i, e) in enumerate(exps):
    (dw, ans) = regen(e, env, trace.subexpr_subtrace(i))
    w += dw
    anss.append(ans)
  return (w, anss)

def r_apply(oper, args, trace):
  # type: (SP, List[vv.VentureValue], Trace) -> Tuple[float, vv.VentureValue]
  reg = oper.regenerator()
  (appw, res) = reg(args, trace)
  if isinstance(res, Datum):
    return (appw, res.datum)
  elif isinstance(res, Request):
    (recurw, val) = regen(res.exp, res.env, res.trace)
    return (appw + recurw, val)

print regen(App([Lit(vv.VentureNumber(1)), Lit(vv.VentureNumber(2))]), VentureEnvironment(), Trace())
