from nose import SkipTest
from nose.tools import eq_
from testconfig import config
import math
from numpy.testing import assert_allclose

from venture.test.config import get_ripl, in_backend, gen_in_backend, on_inf_prim, gen_on_inf_prim
from venture.lite.builtin import builtInSPsList
from venture.test.randomized import * # Importing many things, which are closely related to what this is trying to do pylint: disable=wildcard-import, unused-wildcard-import
from venture.lite.psp import NullRequestPSP
from venture.lite.sp import VentureSPRecord
from venture.lite.value import AnyType, VentureValue, vv_dot_product, ZeroType
from venture.lite.mlens import real_lenses
import venture.test.numerical as num
from venture.lite.exception import VentureBuiltinSPMethodError
from venture.lite.utils import FixedRandomness
import venture.value.dicts as v

@in_backend("none")
def testEquality():
  checkTypedProperty(propEquality, AnyType())

def propEquality(value):
  assert value.equal(value)

@in_backend("none")
def testLiteToStack():
  checkTypedProperty(propLiteToStack, AnyType())

def propLiteToStack(val):
  assert val.equal(VentureValue.fromStackDict(val.asStackDict()))

def relevantSPs():
  for (name,sp) in builtInSPsList:
    if isinstance(sp.requestPSP, NullRequestPSP):
      if name not in ['make_csp']: # Placeholder for selecting SPs to do or not do
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
      eq_(answer, carefully(sp.outputPSP.simulate, args))

@gen_in_backend("none")
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
  if isinstance(sp, VentureSPRecord):
    sp, aux = sp.sp, sp.spAux
  else:
    aux = carefully(sp.constructSPAux)
  args = BogusArgs(args_lists[0], aux)
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

@on_inf_prim("none")
def testExpressionFor():
  checkTypedProperty(propExpressionWorks, AnyType())

def propExpressionWorks(value):
  expr = value.expressionFor()
  result = carefully(eval_in_ripl, expr)
  assert value.equal(result)

@on_inf_prim("none")
def testRiplRoundTripThroughStack():
  checkTypedProperty(propRiplRoundTripThroughStack, AnyType())

def propRiplRoundTripThroughStack(value):
  expr = v.quote(value.asStackDict())
  result = carefully(eval_in_ripl, expr)
  assert value.equal(result)

def eval_in_ripl(expr):
  ripl = get_ripl()
  ripl.predict(expr, label="thing")
  return VentureValue.fromStackDict(ripl.report("thing", type=True))

@gen_on_inf_prim("none")
def testRiplSimulate():
  for (name,sp) in relevantSPs():
    if name in ["scope_include", # Because scope_include is
                                 # misannotated as to the true
                                 # permissible types of scopes and
                                 # blocks
                "get_current_environment", # Because BogusArgs gives a bogus environment
                "extend_environment", # Because BogusArgs gives a bogus environment
              ]:
      continue
    if config["get_ripl"] != "lite" and name in [
        ## Expected failures
        "dict", # Because keys and values must be the same length
        "matrix", # Because rows must be the same length
        "lookup", # Because the key must be an integer for sequence lookups
        "get_empty_environment", # Environments can't be rendered to stack dicts
        ## Incompatibilities with Puma
        "eq", # Not implemented for matrices
        "gt", # Not implemented for matrices
        "gte",
        "lt",
        "lte",
        "real", # Not implemented
        "atom_eq", # Not implemented
        "contains", # Not implemented for sequences
        "arange", # Not implemented
        "linspace", # Not implemented
        "diag_matrix", # Not implemented
        "ravel", # Not implemented
        "matrix_mul", # Not implemented
        "repeat", # Not implemented
        "vector_dot", # Not implemented
    ]:
      continue
    if not sp.outputPSP.isRandom():
      yield checkRiplAgreesWithDeterministicSimulate, name, sp

def checkRiplAgreesWithDeterministicSimulate(name, sp):
  checkTypedProperty(propRiplAgreesWithDeterministicSimulate, fully_uncurried_sp_type(sp.venture_type()), name, sp)

def propRiplAgreesWithDeterministicSimulate(args_lists, name, sp):
  """Check that the given SP produces the same answer directly and
through a ripl (applied fully uncurried)."""
  args = BogusArgs(args_lists[0], sp.constructSPAux())
  answer = carefully(sp.outputPSP.simulate, args)
  if isinstance(answer, VentureSPRecord):
    if isinstance(answer.sp.requestPSP, NullRequestPSP):
      if not answer.sp.outputPSP.isRandom():
        args2 = BogusArgs(args_lists[1], answer.spAux)
        ans2 = carefully(answer.sp.outputPSP.simulate, args2)
        inner = [v.symbol(name)] + [val.expressionFor() for val in args_lists[0]]
        expr = [inner] + [val.expressionFor() for val in args_lists[1]]
        assert ans2.equal(carefully(eval_in_ripl, expr))
      else:
        raise SkipTest("Putatively deterministic sp %s returned a random SP" % name)
    else:
      raise SkipTest("Putatively deterministic sp %s returned a requesting SP" % name)
  else:
    expr = [v.symbol(name)] + [val.expressionFor() for val in args_lists[0]]
    assert answer.equal(carefully(eval_in_ripl, expr))

def eval_foreign_sp(name, sp, expr):
  ripl = get_ripl()
  ripl.bind_foreign_sp(name, sp)
  ripl.predict(expr, label="thing")
  return VentureValue.fromStackDict(ripl.report("thing", type=True))

@gen_on_inf_prim("none")
def testForeignInterfaceSimulate():
  for (name,sp) in relevantSPs():
    if name in ["scope_include", # Because scope_include is
                                 # misannotated as to the true
                                 # permissible types of scopes and
                                 # blocks
                "get_current_environment", # Because BogusArgs gives a bogus environment
                "extend_environment", # Because BogusArgs gives a bogus environment
              ]:
      continue
    if config["get_ripl"] != "lite" and name in [
        ## Expected failures
        "dict", # Because keys and values must be the same length
        "matrix", # Because rows must be the same length
        "get_empty_environment", # Environments can't be rendered to stack dicts
    ]:
      continue
    if not sp.outputPSP.isRandom():
      yield checkForeignInterfaceAgreesWithDeterministicSimulate, name, sp

def checkForeignInterfaceAgreesWithDeterministicSimulate(name, sp):
  checkTypedProperty(propForeignInterfaceAgreesWithDeterministicSimulate, fully_uncurried_sp_type(sp.venture_type()), name, sp)

def propForeignInterfaceAgreesWithDeterministicSimulate(args_lists, name, sp):
  """Check that the given SP produces the same answer directly and
through the foreign function interface (applied fully uncurried)."""
  args = BogusArgs(args_lists[0], sp.constructSPAux())
  answer = carefully(sp.outputPSP.simulate, args)
  if isinstance(answer, VentureSPRecord):
    if isinstance(answer.sp.requestPSP, NullRequestPSP):
      if not answer.sp.outputPSP.isRandom():
        args2 = BogusArgs(args_lists[1], answer.spAux)
        ans2 = carefully(answer.sp.outputPSP.simulate, args2)
        inner = [v.symbol("test_sp")] + [val.expressionFor() for val in args_lists[0]]
        expr = [inner] + [val.expressionFor() for val in args_lists[1]]
        assert ans2.equal(carefully(eval_foreign_sp, "test_sp", sp, expr))
      else:
        raise SkipTest("Putatively deterministic sp %s returned a random SP" % name)
    else:
      raise SkipTest("Putatively deterministic sp %s returned a requesting SP" % name)
  else:
    expr = [v.symbol("test_sp")] + [val.expressionFor() for val in args_lists[0]]
    assert answer.equal(carefully(eval_foreign_sp, "test_sp", sp, expr))

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
def testGradientOfLogDensity():
  for (name,sp) in relevantSPs():
    if name not in ["dict", "multivariate_normal", "wishart", "inv_wishart", "categorical",  # TODO
                    "flip", "bernoulli"]: # TODO: Implement ZeroType
      if sp.outputPSP.isRandom(): # TODO Check the ones that are random when curried
        yield checkGradientOfLogDensity, name, sp

def checkGradientOfLogDensity(name, sp):
  ret_type = final_return_type(sp.venture_type())
  args_type = fully_uncurried_sp_type(sp.venture_type())
  checkTypedProperty(propGradientOfLogDensity, (ret_type, args_type), name, sp)

def propGradientOfLogDensity(rnd, name, sp):
  (value, args_lists) = rnd
  if not len(args_lists) == 1:
    raise SkipTest("TODO: Write the code for measuring log density of curried SPs")
  args = BogusArgs(args_lists[0], sp.constructSPAux())
  answer = carefully(sp.outputPSP.logDensity, value, args)
  if math.isnan(answer) or math.isinf(answer):
    raise ArgumentsNotAppropriate("Log density turned out not to be finite")

  try:
    computed_gradient = sp.outputPSP.gradientOfLogDensity(value, args)
  except VentureBuiltinSPMethodError:
    raise SkipTest("%s does not support computing gradient of log density :(" % name)

  def log_d_displacement_func():
    return sp.outputPSP.logDensity(value, args)
  numerical_gradient = carefully(num.gradient_from_lenses, log_d_displacement_func, real_lenses([value, args_lists[0]]))
  assert_gradients_close(numerical_gradient, computed_gradient)

def assert_gradients_close(numerical_gradient, computed_gradient):
  # TODO Make this deal with symbolic zeroes in the computed gradient.
  # Presumably, one way to do that would be to accept the original
  # value, translate it to gradient type, write the components of the
  # numerical gradient into its lenses, and then do a recursive
  # similarity comparison that takes the symbolic zero into account.
  if any([math.isnan(val) or math.isinf(val) for val in numerical_gradient]):
    raise ArgumentsNotAppropriate("Too close to a singularity; Richardson extrapolation gave non-finite derivatve")

  numerical_values_of_computed_gradient = [lens.get() for lens in real_lenses(computed_gradient)]

  assert_allclose(numerical_gradient, numerical_values_of_computed_gradient, rtol=1e-05)

@gen_in_backend("none")
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
  if isinstance(answer, VentureSPRecord):
    if isinstance(answer.sp.requestPSP, NullRequestPSP):
      args2 = BogusArgs(args_lists[1], answer.spAux)
      randomness2 = FixedRandomness()
      with randomness2:
        ans2 = carefully(answer.sp.outputPSP.simulate, args2)
      for _ in range(5):
        with randomness:
          new_ans = carefully(sp.outputPSP.simulate, args)
        with randomness2:
          new_ans2 = carefully(new_ans.sp.outputPSP.simulate, args2)
        eq_(ans2, new_ans2)
    else:
      raise SkipTest("SP %s returned a requesting SP" % name)
  else:
    for _ in range(5):
      with randomness:
        eq_(answer, carefully(sp.outputPSP.simulate, args))

@gen_in_backend("none")
def testGradientOfSimulate():
  for (name,sp) in relevantSPs():
    if name not in ["dict",  # TODO Synthesize dicts to act as the directions
                    "matrix", # TODO Synthesize non-ragged test lists
                    # The gradients of scope_include and scope_exclude
                    # have weird shapes because scope_include and
                    # scope_exclude are weird.
                    "scope_include", "scope_exclude",
                    # The gradients of biplex and lookup have sporadic
                    # symbolic zeroes.
                    "biplex", "lookup",
                    # For some reason, the gradient is too often large
                    # enough to confuse the numerical approximation
                    "tan"
                   ]:
      yield checkGradientOfSimulate, name, sp

def checkGradientOfSimulate(name, sp):
  checkTypedProperty(propGradientOfSimulate, fully_uncurried_sp_type(sp.venture_type()), name, sp)

def asGradient(value):
  return value.map_real(lambda x: x)

def propGradientOfSimulate(args_lists, name, sp):
  if final_return_type(sp.venture_type().gradient_type()).__class__ == ZeroType:
    # Do not test gradients of things that return elements of
    # 0-dimensional vector spaces
    return
  if not len(args_lists) == 1:
    raise SkipTest("TODO: Write the code for testing simulation gradients of curried SPs")
  if name == "mul" and len(args_lists[0]) is not 2:
    raise ArgumentsNotAppropriate("TODO mul only has a gradient in its binary form")
  args = BogusArgs(args_lists[0], sp.constructSPAux())
  randomness = FixedRandomness()
  with randomness:
    value = carefully(sp.outputPSP.simulate, args)

  # Use the value itself as the test direction in order to avoid
  # having to coordinate compound types (like the length of the list
  # that 'list' returns being the same as the number of arguments)
  direction = asGradient(value)
  try:
    computed_gradient = carefully(sp.outputPSP.gradientOfSimulate, args, value, direction)
  except VentureBuiltinSPMethodError:
    raise SkipTest("%s does not support computing gradient of simulate :(" % name)

  def sim_displacement_func():
    with randomness:
      ans = sp.outputPSP.simulate(args)
    return vv_dot_product(direction, asGradient(ans))
  numerical_gradient = carefully(num.gradient_from_lenses, sim_displacement_func, real_lenses(args_lists[0]))
  assert_gradients_close(numerical_gradient, computed_gradient)
