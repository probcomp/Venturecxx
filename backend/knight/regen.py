from typing import List
from typing import NamedTuple
from typing import Tuple

import venture.lite.value as vv 
from venture.lite.env import VentureEnvironment

class Exp(object): pass

# Make classes so that I can inherit from Exp.
# Pylint misunderstands typing.List pylint: disable=unsubscriptable-object, invalid-sequence-index
class App(NamedTuple('App', [('subs', List[Exp])]), Exp): pass
class Var(NamedTuple('Var', [('name', str)]), Exp): pass
class Lit(NamedTuple('Lit', [('val', vv.VentureValue)]), Exp): pass
class Lam(NamedTuple('Lam', [('params', List[str]), ('body', Exp)]), Exp): pass

class Trace(object):
  def subexpr_subtrace(self, index):
    # type: (int) -> Trace
    pass

def regen(exp, env, trace):
  # type: (Exp, VentureEnvironment, Trace) -> Tuple[float, vv.VentureValue]
  if isinstance(exp, App):
    (w, inter) = regen_list(exp.subs, env, trace)
    ans = sum(inter)
    return (w, ans)
  if isinstance(exp, Lit):
    return (0, exp.val)

def regen_list(exps, env, trace):
  # type: (List[Exp], VentureEnvironment, Trace) -> Tuple[float, List[vv.VentureValue]]
  # This is mapM (\e -> regen(e, env, trace)) in the Writer (Sum Double) monad.
  w = 0.0
  anss = []
  for (i, e) in enumerate(exps):
    (dw, ans) = regen(e, env, trace.subexpr_subtrace(i))
    w += dw
    anss.append(ans)
  return (w, anss)
  

print regen(App([Lit(vv.VentureNumber(1)), Lit(vv.VentureNumber(2))]), VentureEnvironment(), Trace())
