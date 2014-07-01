from nose import SkipTest
from nose.tools import eq_
from testconfig import config
import math
from numpy.testing import assert_allclose

from venture.test.config import get_ripl
from venture.lite.builtin import builtInSPsList
from venture.test.randomized import * # Importing many things, which are closely related to what this is trying to do pylint: disable=wildcard-import, unused-wildcard-import
from venture.lite.psp import NullRequestPSP
from venture.lite.sp import VentureSP
from venture.lite.value import AnyType, VentureValue
from venture.lite.mlens import real_lenses
import venture.test.numerical as num
from venture.lite.exception import VentureBuiltinSPMethodError
from venture.lite.utils import FixedRandomness

def testEquality():
  checkTypedProperty(propEquality, AnyType())

def propEquality(value):
  assert value.equal(value)

def testLiteToStack():
  checkTypedProperty(propLiteToStack, AnyType())

def propLiteToStack(v):
  assert v.equal(VentureValue.fromStackDict(v.asStackDict()))

def relevantSPs():
  for (name,sp) in builtInSPsList:
    if isinstance(sp.requestPSP, NullRequestPSP):
      if name not in []: # Placeholder for selecting SPs to do or not do
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

def testExpressionFor():
  if config["get_ripl"] != "lite": raise SkipTest("Round-trip to the ripl only works in Lite")
  checkTypedProperty(propExpressionWorks, AnyType())

def propExpressionWorks(value):
  expr = value.expressionFor()
  result = carefully(eval_in_ripl, expr)
  assert value.equal(result)

def testRiplRoundTripThroughStack():
  if config["get_ripl"] != "lite": raise SkipTest("Round-trip to the ripl only works in Lite")
  checkTypedProperty(propRiplRoundTripThroughStack, AnyType())

def propRiplRoundTripThroughStack(value):
  expr = [{"type":"symbol", "value":"quote"}, value.asStackDict()]
  result = carefully(eval_in_ripl, expr)
  assert value.equal(result)

def eval_in_ripl(expr):
  ripl = get_ripl()
  ripl.predict(expr, label="thing")
  return VentureValue.fromStackDict(ripl.report("thing", type=True))

def testRiplSimulate():
  if config["get_ripl"] != "lite": raise SkipTest("Round-trip to the ripl only works in Lite")
  for (name,sp) in relevantSPs():
    if name not in ["scope_include", # Because scope_include is
                                     # misannotated as to the true
                                     # permissible types of scopes and
                                     # blocks
                    "get_current_environment", # Because BogusArgs gives a bogus environment
                    "extend_environment", # Because BogusArgs gives a bogus environment
                  ]:
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
        inner = [{"type":"symbol", "value":name}] + [v.expressionFor() for v in args_lists[0]]
        expr = [inner] + [v.expressionFor() for v in args_lists[1]]
        assert ans2.equal(carefully(eval_in_ripl, expr))
      else:
        raise SkipTest("Putatively deterministic sp %s returned a random SP" % name)
    else:
      raise SkipTest("Putatively deterministic sp %s returned a requesting SP" % name)
  else:
    expr = [{"type":"symbol", "value":name}] + [v.expressionFor() for v in args_lists[0]]
    assert answer.equal(carefully(eval_in_ripl, expr))

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

def testGradientOfLogDensity():
  for (name,sp) in relevantSPs():
    if name not in ["dict", "multivariate_normal", "wishart", "inv_wishart", "categorical",  # TODO
                    "flip", "bernoulli"]: # TODO: Implement ZeroType
      if sp.outputPSP.isRandom(): # TODO Check the ones that are random when curried
        yield checkGradientOfLogDensity, name, sp

def checkGradientOfLogDensity(name, sp):
  checkTypedProperty(propGradientOfLogDensity, (final_return_type(sp.venture_type()), fully_uncurried_sp_type(sp.venture_type())), name, sp)

def propGradientOfLogDensity(rnd, name, sp):
  (value, args_lists) = rnd
  if not len(args_lists) == 1:
    raise SkipTest("TODO: Write the code for measuring log density of curried SPs")
  answer = carefully(sp.outputPSP.logDensity, value, BogusArgs(args_lists[0], sp.constructSPAux()))
  if math.isnan(answer) or math.isinf(answer):
    raise ArgumentsNotAppropriate("Log density turned out not to be finite")

  try:
    computed_gradient = sp.outputPSP.gradientOfLogDensity(value, BogusArgs(args_lists[0], sp.constructSPAux()))
  except VentureBuiltinSPMethodError:
    raise SkipTest("%s does not support computing gradient of log density :(" % name)

  def log_d_displacement_func(lens):
    def f(h):
      x = lens.get()
      lens.set(x + h)
      ans = carefully(sp.outputPSP.logDensity, value, BogusArgs(args_lists[0], sp.constructSPAux()))
      # Leave the value in the lens undisturbed
      lens.set(x)
      return ans
    return f
  numerical_gradient = [num.richardson(num.derivative(log_d_displacement_func(lens), 0)) for lens in real_lenses([value, args_lists[0]])]
  if any([math.isnan(v) or math.isinf(v) for v in numerical_gradient]):
    raise ArgumentsNotAppropriate("Too close to a singularity; Richardson extrapolation gave non-finite derivatve")

  numerical_values_of_computed_gradient = [lens.get() for lens in real_lenses(computed_gradient)]

  assert_allclose(numerical_gradient, numerical_values_of_computed_gradient, rtol=1e-05)

def testFixingRandomness():
  for (name,sp) in relevantSPs():
    yield checkFixingRandomness, name, sp

def checkFixingRandomness(name, sp):
  checkTypedProperty(propDeterministicWhenFixed, fully_uncurried_sp_type(sp.venture_type()), name, sp)

def propDeterministicWhenFixed(args_lists, name, sp):
  # TODO Abstract out the similarities between this and propDeterministic
  args = BogusArgs(args_lists[0], sp.constructSPAux())
  randomness = FixedRandomness()
  with randomness:
    answer = carefully(sp.outputPSP.simulate, args)
  if isinstance(answer, VentureSP):
    if isinstance(answer.requestPSP, NullRequestPSP):
      args2 = BogusArgs(args_lists[1], answer.constructSPAux())
      randomness2 = FixedRandomness()
      with randomness2:
        ans2 = carefully(answer.outputPSP.simulate, args2)
      for _ in range(5):
        with randomness:
          new_ans = carefully(sp.outputPSP.simulate, args)
        with randomness2:
          new_ans2 = carefully(new_ans.outputPSP.simulate, args2)
        eq_(ans2, new_ans2)
    else:
      raise SkipTest("SP %s returned a requesting SP" % name)
  else:
    for _ in range(5):
      with randomness:
        eq_(answer, carefully(sp.outputPSP.simulate, args))

def testGradientOfSimulate():
  for (name,sp) in relevantSPs():
    if name not in []:
      yield checkGradientOfSimulate, name, sp

def checkGradientOfSimulate(name, sp):
  checkTypedProperty(propGradientOfSimulate, (final_return_type(sp.venture_type().gradient_type()), fully_uncurried_sp_type(sp.venture_type())), name, sp)

def propGradientOfSimulate(rnd, name, sp):
  (direction, args_lists) = rnd
  if direction == 0:
    # Do not test gradients of things that return elements of
    # 0-dimensional vector spaces
    return
  if not len(args_lists) == 1:
    raise SkipTest("TODO: Write the code for testing simulation gradients of curried SPs")
  args = BogusArgs(args_lists[0], sp.constructSPAux())

  value = carefully(sp.outputPSP.simulate, args)
  try:
    computed_gradient = carefully(sp.outputPSP.gradientOfSimulate, args, value, direction)
  except VentureBuiltinSPMethodError:
    raise SkipTest("%s does not support computing gradient of simulate :(" % name)

  # TODO Abstract similarity with code in propGradientOfLogDensity
  def sim_displacement_func(lens):
    # TODO Abstract similarity with log_d_displacement_func
    def f(h):
      x = lens.get()
      lens.set(x + h)
      ans = carefully(sp.outputPSP.simulate, args)
      number = direction.dot(ans)
      # Leave the value in the lens undisturbed
      lens.set(x)
      return number
    return f
  numerical_gradient = [num.richardson(num.derivative(sim_displacement_func(lens), 0)) for lens in real_lenses(args_lists[0])]
  if any([math.isnan(v) or math.isinf(v) for v in numerical_gradient]):
    raise ArgumentsNotAppropriate("Too close to a singularity; Richardson extrapolation gave non-finite derivatve")

  numerical_values_of_computed_gradient = [lens.get() for lens in real_lenses(computed_gradient)]

  assert_allclose(numerical_gradient, numerical_values_of_computed_gradient, rtol=1e-05)
