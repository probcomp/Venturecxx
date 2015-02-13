# Testing the (Python) SP objects standalone

import math
from testconfig import config
from nose.tools import eq_, assert_almost_equal

from venture.test.config import gen_in_backend
from venture.test.randomized import * # Importing many things, which are closely related to what this is trying to do pylint: disable=wildcard-import, unused-wildcard-import
from venture.lite.builtin import builtInSPsList
from venture.lite.psp import NullRequestPSP
from venture.lite.sp import VentureSPRecord
from venture.lite.utils import FixedRandomness

blacklist = ['make_csp', 'apply_function', 'make_gp']

# Select particular SPs to test thus:
# nosetests --tc=relevant:'["foo", "bar", "baz"]'
def relevantSPs():
  for (name,sp) in builtInSPsList:
    if isinstance(sp.requestPSP, NullRequestPSP):
      if "relevant" not in config or config["relevant"] is None or name in config["relevant"]:
        if name not in blacklist: # Placeholder for selecting SPs to do or not do
          yield name, sp

@gen_in_backend("none")
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
    if isinstance(sp, VentureSPRecord):
      sp, aux = sp.sp, sp.spAux
    else:
      aux = carefully(sp.constructSPAux)
    args = BogusArgs(args_lists[0], aux)
    answer = carefully(sp.outputPSP.simulate, args)
    assert answer in type_.return_type
    propTypeCorrect(args_lists[1:], answer, type_.return_type)

@gen_in_backend("none")
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
  if isinstance(answer, VentureSPRecord):
    if isinstance(answer.sp.requestPSP, NullRequestPSP):
      if not answer.sp.outputPSP.isRandom():
        # We don't currently have any curried SPs that are
        # deterministic at both points, so this code never actually
        # runs.
        args2 = BogusArgs(args_lists[1], answer.spAux)
        ans2 = carefully(answer.sp.outputPSP.simulate, args2)
        for _ in range(5):
          new_ans = carefully(sp.outputPSP.simulate, args)
          new_ans2 = carefully(new_ans.sp.outputPSP.simulate, args2)
          eq_(ans2, new_ans2)
      else:
        raise SkipTest("Putatively deterministic sp %s returned a random SP" % name)
    else:
      raise SkipTest("Putatively deterministic sp %s returned a requesting SP" % name)
  else:
    for _ in range(5):
      assert_almost_equal(answer, carefully(sp.outputPSP.simulate, args), places = 10)

@gen_in_backend("none")
def testRandom():
  for (name,sp) in relevantSPs():
    if sp.outputPSP.isRandom():
      if not name in ["make_uc_dir_mult", "categorical", "make_uc_sym_dir_mult",
                      "log_bernoulli", "log_flip",  # Because the default distribution does a bad job of picking arguments at which log_bernoulli's output actually varies.
                      "noisy_id" # Because it intentionally pretends to be random even though it's not.
      ]:
        yield checkRandom, name, sp

def checkRandom(name, sp):
  # Generate five approprite input/output pairs for the sp
  args_type = fully_uncurried_sp_type(sp.venture_type())
  def f(args_lists): return simulate_fully_uncurried(name, sp, args_lists)
  answers = [findAppropriateArguments(f, args_type, 30) for _ in range(5)]

  # Check that it returns different results on repeat applications to
  # at least one of the inputs.
  for answer in answers:
    if answer is None: continue # Appropriate input was not found; skip
    [args, ans, _] = answer
    for _ in range(10):
      ans2 = simulate_fully_uncurried(name, sp, args)
      if not ans2 == ans:
        return True # Output differed on some input: pass

  assert False, "SP deterministically gave i/o pairs %s" % answers

def simulate_fully_uncurried(name, sp, args_lists):
  if isinstance(sp, VentureSPRecord):
    sp, aux = sp.sp, sp.spAux
  else:
    aux = carefully(sp.constructSPAux)
  if not isinstance(sp.requestPSP, NullRequestPSP):
    raise SkipTest("SP %s returned a requesting SP" % name)
  args = BogusArgs(args_lists[0], aux)
  answer = carefully(sp.outputPSP.simulate, args)
  if len(args_lists) == 1:
    return answer
  else:
    return simulate_fully_uncurried(name, answer, args_lists[1:])

@gen_in_backend("none")
def testLogDensityDeterministic():
  for (name,sp) in relevantSPs():
    if name not in ["dict", "multivariate_normal", "wishart", "inv_wishart", "categorical"]: # TODO
      yield checkLogDensityDeterministic, name, sp

def checkLogDensityDeterministic(_name, sp):
  checkTypedProperty(propLogDensityDeterministic, (fully_uncurried_sp_type(sp.venture_type()), final_return_type(sp.venture_type())), sp)

def propLogDensityDeterministic(rnd, sp):
  (args_lists, value) = rnd
  if not len(args_lists) == 1:
    raise SkipTest("TODO: Write the code for measuring log density of curried SPs")
  answer = carefully(sp.outputPSP.logDensity, value, BogusArgs(args_lists[0], sp.constructSPAux()))
  if math.isnan(answer):
    raise ArgumentsNotAppropriate("Log density turned out to be NaN")
  for _ in range(5):
    eq_(answer, carefully(sp.outputPSP.logDensity, value, BogusArgs(args_lists[0], sp.constructSPAux())))

@gen_in_backend("none")
def testFixingRandomness():
  for (name,sp) in relevantSPs():
    yield checkFixingRandomness, name, sp

def checkFixingRandomness(name, sp):
  checkTypedProperty(propDeterministicWhenFixed, fully_uncurried_sp_type(sp.venture_type()), name, sp)

def propDeterministicWhenFixed(args_lists, name, sp):
  randomness = FixedRandomness()
  with randomness:
    answer = simulate_fully_uncurried(name, sp, args_lists)
  for _ in range(5):
    with randomness:
      eq_(answer, simulate_fully_uncurried(name, sp, args_lists))
