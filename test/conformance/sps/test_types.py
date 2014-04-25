from venture.lite.builtin import builtInSPsList
from venture.test import random_values as r
from venture.test.randomized import *
from venture.lite.psp import NullRequestPSP
from nose import SkipTest
from nose.tools import eq_

def testTypes():
  for (name,sp) in builtInSPsList():
    if isinstance(sp.requestPSP, NullRequestPSP):
      yield propTypeCorrect, name, sp

def propTypeCorrect(_name, sp):
  type_ = sp.venture_type()
  checkTypedProperty(helpPropTypeCorrect, fully_uncurried_sp_type(type_), sp, type_)

def helpPropTypeCorrect(args_lists, sp, type_):
  if len(args_lists) == 0:
    pass # OK
  else:
    args = r.BogusArgs(args_lists[0], sp.constructSPAux())
    answer = carefully(sp.outputPSP.simulate, args)
    assert answer in type_.return_type
    helpPropTypeCorrect(args_lists[1:], answer, type_.return_type)

def testRandomMark():
  for (name,sp) in builtInSPsList():
    if isinstance(sp.requestPSP, NullRequestPSP):
      yield propRandomAnnotated, name, sp

def propRandomAnnotated(name, sp):
  checkTypedProperty(helpPropRandomAnnotated, sp.venture_type().args_types, name, sp)

def helpPropRandomAnnotated(args_list, name, sp):
  args = r.BogusArgs(args_list, sp.constructSPAux())
  answer = carefully(sp.outputPSP.simulate, args)
  if not sp.outputPSP.isRandom():
    for _ in range(5):
      eq_(answer, carefully(sp.outputPSP.simulate, args))
  else:
    raise SkipTest("%s claims to be random" % name)
