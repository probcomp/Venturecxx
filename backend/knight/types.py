from collections import OrderedDict

from typing import Callable
from typing import List
from typing import NamedTuple
from typing import Tuple
from typing import Union
from typing import Optional
from typing import cast

import venture.lite.value as vv 
from venture.lite.env import VentureEnvironment

class Exp(object): pass

# Make classes so that I can inherit from Exp.
# Pylint misunderstands typing.List
# pylint: disable=unsubscriptable-object, invalid-sequence-index
class App(NamedTuple('App', [('subs', List[Exp])]), Exp): pass
class Var(NamedTuple('Var', [('name', str)]), Exp): pass
class Lit(NamedTuple('Lit', [('val', vv.VentureValue)]), Exp): pass
class Lam(NamedTuple('Lam', [('params', List[str]), ('body', Exp)]), Exp): pass

class Trace(vv.VentureValue):
  def __init__(self):
    # type: () -> None
    self.value = None # type: Optional[vv.VentureValue]
    self.subtraces = OrderedDict() # type: OrderedDict[vv.VentureValue, Trace]

  def subtrace(self, key):
    # type: (vv.VentureValue) -> Trace
    if key not in self.subtraces:
      self.subtraces[key] = Trace()
    return self.subtraces[key]

  def subexpr_subtrace(self, index):
    # type: (int) -> Trace
    return self.subtrace(vv.VentureInteger(index))

  def application_subtrace(self):
    # type: () -> Trace
    return self.subtrace(vv.VentureSymbol("app"))

  def has(self):
    # type: () -> bool
    return self.value is not None

  def get(self):
    # type: () -> vv.VentureValue
    assert self.value is not None
    return self.value

  def set(self, value):
    # type: (vv.VentureValue) -> None
    self.value = value

Datum = NamedTuple('Datum', [('datum', vv.VentureValue)])
Request = NamedTuple('Request', [('exp', Exp), ('env', VentureEnvironment[vv.VentureValue]),
                                 ('constraints', Trace), ('interventions', Trace)])

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
  if isinstance(exp.subs[0], Var):
    if exp.subs[0].name == "make_csp":
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
