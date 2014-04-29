from venture.lite.builtin import builtInSPsList
from venture.test.randomized import * # Importing many things, which are closely related to what this is trying to do pylint: disable=wildcard-import, unused-wildcard-import
from venture.lite.psp import NullRequestPSP
from nose import SkipTest
from nose.tools import eq_
from venture.lite.sp import VentureSP

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

def testDeterministic():
  for (name,sp) in builtInSPsList():
    if isinstance(sp.requestPSP, NullRequestPSP):
      if not sp.outputPSP.isRandom():
        yield checkDeterministic, name, sp

def checkDeterministic(name, sp):
  checkTypedProperty(propDeterministic, fully_uncurried_sp_type(sp.venture_type()), name, sp)

def propDeterministic(args_lists, name, sp):
  args = BogusArgs(args_lists[0], sp.constructSPAux())
  answer = carefully(sp.outputPSP.simulate, args)
  if isinstance(answer, VentureSP):
    if isinstance(answer.requestPSP, NullRequestPSP):
      if not answer.outputPSP.isRandom():
        args2 = BogusArgs(args_lists[1], answer.constructSPAux())
        ans2 = carefully(answer.outputPSP.simulate, args2)
        for _ in range(5):
          new_ans = carefully(sp.outputPSP.simulate, args)
          new_ans2 = carefully(new_ans.outputPSP.simulate, args2)
          eq_(ans2, new_ans2)
      else:
        raise SkipTest("Putatively deterministic sp %s returned a random SP" % name)
    else:
      raise SkipTest("Putatively deterministic sp %s returned a requesting SP" % name)
  else:
    for _ in range(5):
      eq_(answer, carefully(sp.outputPSP.simulate, args))

def testRandom():
  for (name,sp) in builtInSPsList():
    if isinstance(sp.requestPSP, NullRequestPSP):
      if sp.outputPSP.isRandom():
        yield checkRandom, name, sp

def checkRandom(_name, sp):
  # I want the name to appear in the nose arg list
  checkTypedProperty(propRandom, fully_uncurried_sp_type(sp.venture_type()), sp)

def evaluate_fully_uncurried(sp, args_lists):
  args = BogusArgs(args_lists[0], sp.constructSPAux())
  answer = carefully(sp.outputPSP.simulate, args)
  if len(args_lists) == 1:
    return answer
  else:
    return evaluate_fully_uncurried(answer, args_lists[1:])

def propRandom(args_lists, sp):
  answer = evaluate_fully_uncurried(sp, args_lists)
  for _ in range(10):
    ans2 = evaluate_fully_uncurried(sp, args_lists)
    if not ans2 == answer:
      return True
  assert False, "Result turned out the same every time"
