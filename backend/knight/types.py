from typing import List
from typing import NamedTuple
from typing import Optional
from typing import Tuple
from typing import Union
from typing import cast

from venture.lite.env import VentureEnvironment
import venture.lite.value as vv

from venture.knight.trace import Trace

class Exp(object): pass

# Make classes so that I can inherit from Exp.
# Pylint misunderstands typing.List
# pylint: disable=unsubscriptable-object, invalid-sequence-index
class App(NamedTuple('App', [('subs', List[Exp])]), Exp): pass
class Var(NamedTuple('Var', [('name', str)]), Exp): pass
class Lit(NamedTuple('Lit', [('val', vv.VentureValue)]), Exp): pass
class Lam(NamedTuple('Lam', [('params', List[str]), ('body', Exp)]), Exp): pass
class Seq(NamedTuple('Seq', [('subs', List[Exp])]), Exp): pass
class Def(NamedTuple('Def', [('pat', Exp), ('expr', Exp)]), Exp): pass
class Spl(NamedTuple('Spl', [('sub', Exp)]), Exp): pass
class Tra(NamedTuple('Tra', [('top', Optional[Exp]), ('entries', List[Tuple[Exp, Exp]])]), Exp): pass
class Tup(NamedTuple('Tup', [('subs', List[Exp])]), Exp): pass

Datum = NamedTuple('Datum', [('datum', vv.VentureValue)])
Request = NamedTuple('Request', [('exp', Exp), ('env', VentureEnvironment[vv.VentureValue]),
                                 ('target', Trace), ('mechanism', Trace)])

RegenResult = Union[Datum, Request]

def stack_dict_to_exp(form):
  # type: (object) -> Exp
  if isinstance(form, (list, tuple)):
    candidate = App(map(stack_dict_to_exp, form))
    return convert_lambda_terms(candidate)
  if isinstance(form, basestring):
    return Var(str(form))
  if isinstance(form, dict):
    # Symbol or Literal object
    val = vv.VentureValue.fromStackDict(form)
    if isinstance(val, vv.VentureSymbol):
      return Var(val.getSymbol())
    return Lit(val)
  assert False

def convert_lambda_terms(exp):
  # type: (App) -> Exp
  if len(exp.subs) < 1:
    return exp
  if isinstance(exp.subs[0], Var):
    if exp.subs[0].name == "make_csp":
      assert len(exp.subs) == 3
      return Lam(extract_quoted_param_list(exp.subs[1]), extract_quoted(exp.subs[2]))
    else:
      return exp
  else:
    return exp

def extract_quoted(exp):
  # type: (Exp) -> Exp
  assert isinstance(exp, App)
  assert isinstance(exp.subs[0], Var)
  assert exp.subs[0].name == "quote"
  return exp.subs[1]

def extract_quoted_param_list(exp):
  # type: (Exp) -> List[str]
  res = extract_quoted(exp)
  assert isinstance(res, App)
  subs = cast(List[Var], res.subs)
  for sub in subs:
    assert isinstance(sub, Var)
  return [v.name for v in subs]
