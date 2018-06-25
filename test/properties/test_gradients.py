# Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

import math
import random

from nose.tools import assert_almost_equal
from numpy.testing import assert_allclose

from venture.test.flaky import flaky
from venture.test.config import broken_in
from venture.test.config import gen_broken_in
from venture.test.config import gen_in_backend
from venture.test.config import gen_on_inf_prim
from venture.test.config import get_ripl
from venture.test.config import on_inf_prim
from venture.test.properties.test_sps import relevantSPs
from venture.test.randomized import * # Importing many things, which are closely related to what this is trying to do pylint: disable=wildcard-import, unused-wildcard-import
from venture.lite.exception import VentureBuiltinSPMethodError
from venture.lite.mlens import real_lenses
from venture.lite.sp_use import MockArgs
from venture.lite.sp_use import gradientOfLogDensity
from venture.lite.sp_use import logDensity
import venture.lite.value as vv
import venture.lite.types as t
from venture.lite.utils import FixedRandomness
import venture.test.numerical as num

@gen_in_backend("none")
def testGradientOfLogDensity():
  for (name,sp) in relevantSPs():
    if name not in [
        "bernoulli",            # TODO: Implement ZeroType
        "categorical",          # TODO
        "dict",
        "flip",                 # TODO: Implement ZeroType
        "lognormal",            # bounded support: (0, +\infty)
        "inv_wishart",          # TODO
        "multivariate_normal",  # TODO
        "wishart",              # TODO
    ]:
      # TODO Check the ones that are random when curried
      if sp.outputPSP.isRandom():
        yield checkGradientOfLogDensity, name, sp

def checkGradientOfLogDensity(name, sp):
  ret_type = final_return_type(sp.venture_type())
  args_type = fully_uncurried_sp_type(sp.venture_type())
  checkTypedProperty(propGradientOfLogDensity, (ret_type, args_type), name, sp)

def propGradientOfLogDensity(rnd, name, sp):
  (value, args_lists) = rnd
  if not len(args_lists) == 1:
    raise SkipTest("TODO: Write the code for measuring log density of curried SPs")
  answer = carefully(logDensity(sp), value, args_lists[0])
  if math.isnan(answer) or math.isinf(answer):
    raise ArgumentsNotAppropriate("Log density turned out not to be finite")

  expected_grad_type = sp.venture_type().gradient_type().args_types
  try:
    computed_gradient = gradientOfLogDensity(sp)(value, args_lists[0])
    (dvalue, dargs) = computed_gradient
    for (g, tp) in [(dvalue, sp.venture_type().gradient_type().return_type)] + zip(dargs, expected_grad_type):
      if g == 0:
        pass # OK
      else:
        assert g in tp
  except VentureBuiltinSPMethodError:
    raise SkipTest("%s does not support computing gradient of log density :(" % name)

  def log_d_displacement_func():
    return logDensity(sp)(value, args_lists[0])
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
    if name in ["dict",  # TODO Synthesize dicts to act as the directions
                "matrix", # TODO Synthesize non-ragged test lists
                # The gradients of tag and tag_exclude
                # have weird shapes because tag and
                # tag_exclude are weird.
                "tag", "tag_exclude",
                # The gradients of biplex and lookup have sporadic
                # symbolic zeroes.
                "biplex", "lookup",
                # TODO The gradient of floor is a symbolic zero
                # with a continuous-looking output space, which
                # confuses this code
                "floor",
                # For some reason, the gradient is too often large
                # enough to confuse the numerical approximation
                "tan",
                # Synthesizing inputs and dealing with them gets
                # confused; and the gradient is not very interesting
                "exactly",
    ]:
      continue
    elif name.startswith('gp_cov_') or name.startswith('gp_mean_'):
      # XXX No gradients yet in Gaussian processes -- Github issue #433.
      continue
    elif name in ["div", "gamma"]:
      # Because of numerical artifacts when test arguments are near zero
      yield checkFlakyGradientOfSimulate, name, sp
    else:
      yield checkGradientOfSimulate, name, sp

def checkGradientOfSimulate(name, sp):
  checkTypedProperty(propGradientOfSimulate, fully_uncurried_sp_type(sp.venture_type()), name, sp)

@flaky
def checkFlakyGradientOfSimulate(name, sp):
  checkGradientOfSimulate(name, sp)

def asGradient(value):
  return value.map_real(lambda x: x)

def propGradientOfSimulate(args_lists, name, sp):
  if final_return_type(sp.venture_type().gradient_type()).__class__ == t.ZeroType:
    # Do not test gradients of things that return elements of
    # 0-dimensional vector spaces
    return
  if not len(args_lists) == 1:
    raise SkipTest("TODO: Write the code for testing simulation gradients of curried SPs")
  if name == "mul" and len(args_lists[0]) is not 2:
    raise ArgumentsNotAppropriate("TODO mul only has a gradient in its binary form")
  py_rng = random.Random()
  np_rng = npr.RandomState()
  args = MockArgs(args_lists[0], sp.constructSPAux(), py_rng, np_rng)
  randomness = FixedRandomness(py_rng, np_rng)
  with randomness:
    value = carefully(sp.outputPSP.simulate, args)

  # Use the value itself as the test direction in order to avoid
  # having to coordinate compound types (like the length of the list
  # that 'list' returns being the same as the number of arguments)
  direction = asGradient(value)
  expected_grad_type = sp.venture_type().gradient_type().args_types
  try:
    computed_gradient = carefully(sp.outputPSP.gradientOfSimulate, args, value, direction)
    for (g, tp) in zip(computed_gradient, expected_grad_type):
      if g == 0:
        pass # OK
      else:
        assert g in tp
  except VentureBuiltinSPMethodError:
    raise SkipTest("%s does not support computing gradient of simulate :(" % name)

  def sim_displacement_func():
    with randomness:
      ans = sp.outputPSP.simulate(args)
    return vv.vv_dot_product(direction, asGradient(ans))
  numerical_gradient = carefully(num.gradient_from_lenses, sim_displacement_func, real_lenses(args_lists[0]))
  assert_gradients_close(numerical_gradient, computed_gradient)

@broken_in("puma", "Puma doesn't have gradients")
@on_inf_prim("gradient_ascent")
def testGradientOfSimulateOfLookup():
  from venture.lite.sp_registry import builtInSPs
  sp = builtInSPs()["lookup"]
  args = [vv.VentureArray([vv.VentureNumber(0), vv.VentureNumber(0)]), vv.VentureNumber(1)]
  grad = sp.outputPSP.gradientOfSimulate(
    MockArgs(args, sp.constructSPAux()), vv.VentureNumber(0), vv.VentureNumber(1))
  assert grad[0].lookup(vv.VentureNumber(0)) == 0
  assert grad[0].lookup(vv.VentureNumber(1)) == vv.VentureNumber(1)
  assert grad[1] == 0

@broken_in("puma", "Puma doesn't have gradients")
@on_inf_prim("gradient_ascent")
def testGradientOfSimulateOfLookup2():
  from venture.lite.sp_registry import builtInSPs
  sp = builtInSPs()["lookup"]
  args = [vv.VentureArrayUnboxed([0, 0], t.Number), vv.VentureNumber(1)]
  grad = sp.outputPSP.gradientOfSimulate(
    MockArgs(args, sp.constructSPAux()), vv.VentureNumber(0), vv.VentureNumber(1))
  assert grad[0].lookup(vv.VentureNumber(0)) == vv.VentureNumber(0)
  assert grad[0].lookup(vv.VentureNumber(1)) == vv.VentureNumber(1)
  assert grad[1] == 0

@gen_broken_in("puma", "Puma doesn't have gradients")
@gen_on_inf_prim("gradient_ascent")
def testGradientOfLogDensityOfDataSmoke():
  models = [("(make_crp a)", ["atom<1>", "atom<2>"]),
            ("(make_suff_stat_normal a 1)", [2]),
            ("(make_dir_cat (vector a 1) (list 1 2))", ["1"]),
            ("(make_sym_dir_cat a 2 (list 1 2))", ["1", "2"]),
            ("(make_beta_bernoulli a 1)", [True]),
            ("(make_suff_stat_bernoulli a)", [True]),
            ("(make_suff_stat_poisson a)", [2])
          ]
  for (expr, vals) in models:
    yield checkGradientExists, expr, vals

def checkGradientExists(expr, vals):
  ripl = get_ripl()
  ripl.assume("a", "(uniform_continuous 0 1)")
  value = ripl.sample("a")
  ripl.assume("f", expr)
  for val in vals:
    ripl.observe("(f)", val)
  ripl.infer("(gradient_ascent default all 0.01 1 1)")
  new_value = ripl.sample("a")
  assert value != new_value, "Gradient was not transmitted to prior"


def prep_coin_flipping_ripl():
  """Prepare the ripl for the two gradient tests below."""
  ripl = get_ripl()
  ripl.assume("weight", "(beta 1 1)")
  ripl.force("weight", 0.5)
  ripl.assume("coin", "(make_suff_stat_bernoulli weight)")
  ripl.observe("(coin)", True)
  ripl.observe("(coin)", True)
  return ripl

@broken_in('puma', "Gradients only implemented in Lite.")
@on_inf_prim("gradient_ascent")
def test_gradient_with_default_args():
  """Test whether default args for gradients work using old inf syntax."""
  ripl = prep_coin_flipping_ripl()
  # Assuming steps=1 and transistions=1 by default.
  ripl.infer("(gradient_ascent default all 0.03)")
  # Test wether the above is equivalent to taking exactly one step.
  assert_almost_equal(ripl.sample("weight"), 0.62)

@broken_in('puma', "Gradients only implemented in Lite.")
@on_inf_prim("gradient_ascent")
def test_gradient_with_default_args_subproblem_syntax():
  """Test whether default args for gradients work using subproblem syntax."""
  ripl = prep_coin_flipping_ripl()
  # Assuming steps=1 and transistions=1 by default.
  ripl.set_mode('venture_script')
  ripl.infer('gradient_ascent(minimal_subproblem(/*), 0.03)')
  # Test wether the above is equivalent to taking exactly one step.
  assert_almost_equal(ripl.sample("weight"), 0.62)
