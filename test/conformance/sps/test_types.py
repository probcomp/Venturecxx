from nose import SkipTest
from nose.tools import eq_

from venture.test.config import get_ripl
from venture.lite.builtin import builtInSPsList
from venture.test.randomized import * # Importing many things, which are closely related to what this is trying to do pylint: disable=wildcard-import, unused-wildcard-import
from venture.lite.psp import NullRequestPSP
from venture.lite.sp import VentureSP

def relevantSPs():
  for (name,sp) in builtInSPsList():
    if isinstance(sp.requestPSP, NullRequestPSP):
      if not name in ["wishart", "inv_wishart"]:
        yield name, sp

def testTypes():
  for (name,sp) in relevantSPs():
    yield checkTypeCorrect, name, sp

def checkTypeCorrect(_name, sp):
  type_ = sp.venture_type()
  checkTypedProperty(propTypeCorrect, fully_uncurried_sp_type(type_), sp, type_)

def propTypeCorrect(args_lists, sp, type_):
  """Check that the successive return values of the given SP (when
applied fully uncurried) match the expected types."""
  if len(args_lists) == 0:
    pass # OK
  else:
    args = BogusArgs(args_lists[0], sp.constructSPAux())
    answer = carefully(sp.outputPSP.simulate, args)
    assert answer in type_.return_type
    propTypeCorrect(args_lists[1:], answer, type_.return_type)

def testDeterministic():
  for (name,sp) in relevantSPs():
    if not sp.outputPSP.isRandom():
      yield checkDeterministic, name, sp

def checkDeterministic(name, sp):
  checkTypedProperty(propDeterministic, fully_uncurried_sp_type(sp.venture_type()), name, sp)

def propDeterministic(args_lists, name, sp):
  """Check that the given SP returns the same answer every time (applied
fully uncurried)."""
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
  for (name,sp) in relevantSPs():
    if sp.outputPSP.isRandom():
      if not name in ["make_uc_dir_mult", "categorical", "make_uc_sym_dir_mult"]:
        yield checkRandom, name, sp

def checkRandom(_name, sp):
  # I take the name because I want it to appear in the nose arg list
  args_type = fully_uncurried_sp_type(sp.venture_type())
  checkTypedProperty(propRandom, [args_type for _ in range(5)] , sp)

def evaluate_fully_uncurried(sp, args_lists):
  args = BogusArgs(args_lists[0], sp.constructSPAux())
  answer = carefully(sp.outputPSP.simulate, args)
  if len(args_lists) == 1:
    return answer
  else:
    return evaluate_fully_uncurried(answer, args_lists[1:])

def propRandom(args_listss, sp):
  """Check that the given SP is random on at least one set of arguments."""
  answers = []
  for args_lists in args_listss:
    try:
      answer = evaluate_fully_uncurried(sp, args_lists)
      answers.append(answer)
      for _ in range(10):
        ans2 = evaluate_fully_uncurried(sp, args_lists)
        if not ans2 == answer:
          return True
    except ArgumentsNotAppropriate:
      # This complication serves the purpose of not decreasing the
      # acceptance rate of the search of appropriate arguments to the
      # SP, while allowing the SP to redeem its claims of randomness
      # on additional arguments if they are available.
      if answers == []:
        raise
      else:
        answers.append("Inappropriate arguments")
        continue
  assert False, "SP deterministically returned %s (parallel to arguments)" % answers

def testRiplSimulate():
  for (name,sp) in relevantSPs():
    if not sp.outputPSP.isRandom():
      yield checkRiplAgreesWithDeterministicSimulate, name, sp

def checkRiplAgreesWithDeterministicSimulate(name, sp):
  checkTypedProperty(propRiplAgreesWithDeterministicSimulate, fully_uncurried_sp_type(sp.venture_type()), name, sp)

def propRiplAgreesWithDeterministicSimulate(args_lists, name, sp):
  """Check that the given SP produces the same answer directly and
through a ripl (applied fully uncurried)."""
  args = BogusArgs(args_lists[0], sp.constructSPAux())
  answer = carefully(sp.outputPSP.simulate, args)
  if isinstance(answer, VentureSP):
    if isinstance(answer.requestPSP, NullRequestPSP):
      if not answer.outputPSP.isRandom():
        args2 = BogusArgs(args_lists[1], answer.constructSPAux())
        ans2 = carefully(answer.outputPSP.simulate, args2)
        inner = [name] + [["quote", v.asStackDict(None)] for v in args_lists[0]]
        expr = [inner] + [["quote", v.asStackDict(None)] for v in args_lists[1]]
        eq_(ans2, carefully(get_ripl().predict, expr))
      else:
        raise SkipTest("Putatively deterministic sp %s returned a random SP" % name)
    else:
      raise SkipTest("Putatively deterministic sp %s returned a requesting SP" % name)
  else:
    expr = [name] + [["quote", v.asStackDict(None)] for v in args_lists[0]]
    eq_(answer.asStackDict(None)["value"], carefully(get_ripl().predict, expr))
