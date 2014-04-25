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

def appropriate_arguments(sp, type_, budget=20):
  for _ in range(budget):
    args = r.random_args_for_sp(sp, type_)
    if args is None: continue
    try:
      answer = sp.outputPSP.simulate(args)
      yield args, answer
    except ValueError: continue
    except VentureValueError: continue

def propTypeCorrect(name, sp):
  type_ = sp.venture_type()
  app_ct = 0
  for (_, answer) in appropriate_arguments(sp, type_):
    app_ct += 1
    helpPropTypeCorrect(answer, type_.return_type)
  if app_ct == 0:
    raise SkipTest("Could not find appropriate args for %s" % name)

def helpPropTypeCorrect(answer, type_):
  assert answer in type_
  if isinstance(type_, SPType):
    for (_, ans2) in appropriate_arguments(answer, type_, budget=1):
      helpPropTypeCorrect(ans2, type_.return_type)
