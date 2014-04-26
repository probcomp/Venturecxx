from venture.lite.builtin import builtInSPsList
from venture.test.randomized import *
from venture.lite.psp import NullRequestPSP
from nose import SkipTest
from nose.tools import eq_

def testTypes():
  for (name,sp) in builtInSPsList():
    if isinstance(sp.requestPSP, NullRequestPSP):
      yield checkTypeCorrect, name, sp

def checkTypeCorrect(_name, sp):
  type_ = sp.venture_type()
  checkTypedProperty(propTypeCorrect, fully_uncurried_sp_type(type_), sp, type_)

def propTypeCorrect(args_lists, sp, type_):
  if len(args_lists) == 0:
    pass # OK
  else:
    args = BogusArgs(args_lists[0], sp.constructSPAux())
    answer = carefully(sp.outputPSP.simulate, args)
    assert answer in type_.return_type
    propTypeCorrect(args_lists[1:], answer, type_.return_type)

def testRandomMark():
  for (name,sp) in builtInSPsList():
    if isinstance(sp.requestPSP, NullRequestPSP):
      yield checkRandomAnnotated, name, sp

def checkRandomAnnotated(name, sp):
  checkTypedProperty(propRandomAnnotated, sp_args_type(sp.venture_type()), name, sp)

def propRandomAnnotated(args_list, name, sp):
  args = BogusArgs(args_list, sp.constructSPAux())
  answer = carefully(sp.outputPSP.simulate, args)
  if not sp.outputPSP.isRandom():
    for _ in range(5):
      eq_(answer, carefully(sp.outputPSP.simulate, args))
  else:
    raise SkipTest("%s claims to be random" % name)
