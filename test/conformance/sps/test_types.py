from venture.lite.builtin import builtInSPsList
from venture.test import randomized as r
from venture.lite.psp import NullRequestPSP
from venture.lite.exception import VentureValueError
from nose import SkipTest

def testTypes():
  for (name,sp) in builtInSPsList():
    if isinstance(sp.requestPSP, NullRequestPSP):
      yield propTypeCorrect, name, sp

def propTypeCorrect(name, sp):
  app_ct = 0
  answer = None
  for _ in range(20):
    args = r.random_args_for_sp(sp)
    if args is None:
      continue
    try:
      answer = sp.outputPSP.simulate(args)
      appropriate = True
      app_ct += 1
    except ValueError:
      appropriate = False
    except VentureValueError:
      appropriate = False
    if appropriate:
      assert answer in sp.venture_type().return_type
  if app_ct == 0:
    raise SkipTest("Could not find appropriate args for %s" % name)
