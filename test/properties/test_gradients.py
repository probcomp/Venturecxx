import math
from numpy.testing import assert_allclose

from venture.test.config import gen_in_backend
from venture.test.randomized import * # Importing many things, which are closely related to what this is trying to do pylint: disable=wildcard-import, unused-wildcard-import
from venture.lite.exception import VentureBuiltinSPMethodError
from venture.lite.mlens import real_lenses
import venture.lite.value as vv
from venture.lite.utils import FixedRandomness
import venture.test.numerical as num

from test_sps import relevantSPs

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
                    # TODO The gradient of floor is a symbolic zero
                    # with a continuous-looking output space, which
                    # confuses this code
                    "floor",
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
  if final_return_type(sp.venture_type().gradient_type()).__class__ == vv.ZeroType:
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
    return vv.vv_dot_product(direction, asGradient(ans))
  numerical_gradient = carefully(num.gradient_from_lenses, sim_displacement_func, real_lenses(args_lists[0]))
  assert_gradients_close(numerical_gradient, computed_gradient)
