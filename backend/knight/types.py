from typing import Callable
from typing import List
from typing import NamedTuple
from typing import Tuple
from typing import Union

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
  def application_subtrace(self):
    # type: () -> Trace
    pass
  def root_constrained(self):
    # type: () -> bool
    pass
  def get_at_root(self):
    # type: () -> vv.VentureValue
    pass

Datum = NamedTuple('Datum', [('datum', vv.VentureValue)])
Request = NamedTuple('Request', [('exp', Exp), ('env', VentureEnvironment[vv.VentureValue]), ('trace', Trace)])

RegenResult = Union[Datum, Request]
