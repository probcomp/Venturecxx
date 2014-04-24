from venture.lite.builtin import builtInSPsList
from venture.test import randomized as r
from venture.lite.psp import NullRequestPSP
from venture.lite.exception import VentureValueError
from venture.lite.sp import SPType
from nose import SkipTest

def testTypes():
  for (name,sp) in builtInSPsList():
    if isinstance(sp.requestPSP, NullRequestPSP):
      yield propTypeCorrect, name, sp

def propTypeCorrect(name, sp):
  app_ct = 0
  for _ in range(20):
    try:
      if helpPropTypeCorrect(sp, sp.venture_type()):
        app_ct += 1
    except ValueError: pass
    except VentureValueError: pass
  if app_ct == 0:
    raise SkipTest("Could not find appropriate args for %s" % name)

def helpPropTypeCorrect(sp, the_type):
  args = r.random_args_for_sp(the_type)
  if args is None:
    return False # Not appropriate arguments
  answer = sp.outputPSP.simulate(args)
  assert answer in the_type.return_type
  if isinstance(the_type.return_type, SPType):
    return helpPropTypeCorrect(answer, the_type.return_type)
  else:
    return True
