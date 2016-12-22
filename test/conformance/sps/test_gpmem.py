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

from collections import OrderedDict
from nose import SkipTest
from nose.tools import eq_
import numpy as np
import numpy.random as npr

from venture.test.config import broken_in
from venture.test.config import collectSamples
from venture.test.config import default_num_samples
from venture.test.config import get_ripl
from venture.test.config import in_backend
from venture.test.config import on_inf_prim
from venture.test.stats import reportKnownGaussian
from venture.test.stats import reportKnownMean
from venture.test.stats import reportPearsonIndependence
from venture.test.stats import statisticalTest
from venture.test.stats import stochasticTest
import venture.lite.covariance as cov
import venture.lite.gp as gp
import venture.lite.value as v

def prep_ripl(ripl):
  ripl.assume('zero', "(gp_mean_const 0.)")
  ripl.assume('sq_exp', "(gp_cov_se 1.)")

def array(xs):
  return v.VentureArrayUnboxed(np.array(xs), gp.xType)

@broken_in('puma', "Puma does not define the gaussian process builtins")
@on_inf_prim('none')
def test_create_gpmem_package_church():
  ripl = get_ripl()
  prep_ripl(ripl)
  prog = """
    [assume f (lambda (x) x)]
    [assume package ((allocate_gpmem) f zero sq_exp)]
  """
  ripl.execute_program(prog)

def test_predict_f_compute_gpmem_package_church():
  ripl = get_ripl()
  prep_ripl(ripl)
  prog = """
    [assume f (lambda (x) x)]
    [assume package ((allocate_gpmem) f zero sq_exp)]
    [predict ((first package) 12.6)]
  """
  ripl.execute_program(prog)

def test_sample_f_emu_gpmem_package_church():
  ripl = get_ripl()
  prep_ripl(ripl)
  prog = """
    [assume f (lambda (x) x)]
    [assume package ((allocate_gpmem) f zero sq_exp)]
    (sample ((second package) 12.8))
  """
  ripl.execute_program(prog)

def test_observe_f_emu_gpmem_package_church():
  ripl = get_ripl()
  prep_ripl(ripl)
  prog = """
    [assume f (lambda (x) x)]
    [assume package ((allocate_gpmem) f zero sq_exp)]
    (observe ((second package) -3.1) 2.6)
  """
  ripl.execute_program(prog)

@broken_in('puma', "Puma does not define the gaussian process builtins")
@statisticalTest
def testGPMem_mean1(seed):
  ripl = get_ripl(seed=seed)
  prep_ripl(ripl)
  prog = """
    [assume f (lambda (x) x)]
    [assume package ((allocate_gpmem) f zero sq_exp)]
    [assume f_emu (second package)]
  """
  ripl.execute_program(prog)

  ripl.predict("(f_emu 0)",label="pid")

  predictions = collectSamples(ripl,"pid",num_samples=default_num_samples(2))

  return reportKnownGaussian(0, 1, predictions)

@broken_in('puma', "Puma does not define the gaussian process builtins")
@statisticalTest
def testGPMem_mean2(seed):
  ripl = get_ripl(seed=seed)
  prep_ripl(ripl)
  prog = """
    [assume f (lambda (x) x)]
    [assume package ((allocate_gpmem) f zero sq_exp)]
    [assume f_emu (second package)]
  """
  ripl.execute_program(prog)

  ripl.observe('(f_emu (array -1 1))', array([-1, 1]))

  ripl.predict("(f_emu 0)",label="pid")

  predictions = collectSamples(ripl,"pid")

  # TODO: variance
  return reportKnownMean(0, predictions)

@broken_in('puma', "Puma does not define the gaussian process builtins")
@on_inf_prim('mh')
def testHyperparameterInferenceSmoke():
  ripl = get_ripl()
  ripl.execute_program("""\
      [assume mean (gp_mean_const 0.)]
      [assume a (tag (quote hypers ) 0 (inv_gamma 2 5))]
      [assume l (tag (quote hypers ) 1 (inv_gamma 5 50))]
      [assume cov (gp_cov_scale a (gp_cov_se (* l l)))]
      [assume f (lambda (x) x)]
      [assume package ((allocate_gpmem) f mean cov)]
      [assume f_emu (second package)]
  """)
  ripl.observe("(f_emu (array 1 2 3))", array([1.1, 2.2, 3.3]))
  ripl.infer("(mh (quote hypers) one 1)")

@broken_in('puma', "Puma does not define the gaussian process builtins")
@on_inf_prim('mh')
def test_second_package_bug():
  """  Testing propagation of hyperparameter inference (second package bug)
  
  See github issue #447
  """
  ripl = get_ripl()
  ripl.assume('mean', '(gp_mean_const 0.)')
  ripl.assume('l', '(tag (quote hypers ) 1 (inv_gamma 5 50))')
  ripl.assume('cov', '(gp_cov_se (* l l))')
  ripl.assume('f', '(lambda (x) x)')
  ripl.assume('package', '((allocate_gpmem) f mean cov)')
  ripl.assume('f_emu', '(second package)')
  ripl.observe('(f_emu (array 1 2 3))', array([1.1, 2.2, 3.3]))

  def get_lengthscale_from_pretty_printed_gp(gp_str):
    """ getting the lengthscale parameter from the printed gp"""
    return  float(gp_str.split('l^2=')[1][:-2])

  l_before_inference = ripl.sample('l')
  strg_sample_f_emu = ripl.sample('f_emu')
  l_before_inference_inside_GP = get_lengthscale_from_pretty_printed_gp(strg_sample_f_emu)
  assert l_before_inference**2 == l_before_inference_inside_GP

  ripl.infer("(mh (quote hypers) one 100)")

  l_after_inference = ripl.sample('l')
  strg_sample_f_emu = ripl.sample('f_emu')
  l_after_inference_inside_GP = get_lengthscale_from_pretty_printed_gp(strg_sample_f_emu)
  assert l_before_inference != l_after_inference, "hyperparameter did not change at all"
  assert l_after_inference**2 == l_after_inference_inside_GP, """
    change of hyperparameters after inference did not propagate to GP"""

@broken_in('puma', "Puma does not define the gaussian process builtins")
@on_inf_prim('mh')
def test_inlining_second_package():
  """  Testing  inlining to fix the second package bug

  """
  ripl = get_ripl()
  ripl.assume('mean', '(gp_mean_const 0.)')
  ripl.assume('l', '(tag (quote hypers ) 1 (inv_gamma 5 50))')
  ripl.assume('cov', '(gp_cov_se (* l l))')
  ripl.assume('f', '(lambda (x) x)')
  ripl.assume('package', '((allocate_gpmem) f mean cov)')
  ripl.observe('((second package) (array 1 2 3))', array([1.1, 2.2, 3.3]))

  def get_lengthscale_from_pretty_printed_gp(gp_str):
    """ getting the lengthscale parameter from the printed gp"""
    return  float(gp_str.split('l^2=')[1][:-2])

  l_before_inference = ripl.sample('l')
  strg_sample_f_emu = ripl.sample('(second package)')
  l_before_inference_inside_GP = get_lengthscale_from_pretty_printed_gp(strg_sample_f_emu)
  assert l_before_inference**2 == l_before_inference_inside_GP

  ripl.infer("(mh (quote hypers) one 100)")

  l_after_inference = ripl.sample('l')
  strg_sample_f_emu = ripl.sample('(second package)')
  l_after_inference_inside_GP = get_lengthscale_from_pretty_printed_gp(strg_sample_f_emu)
  assert l_before_inference != l_after_inference, "hyperparameter did not change at all"
  assert l_after_inference**2 == l_after_inference_inside_GP, """
    change of hyperparameters after inference did not propagate to GP"""

@broken_in('puma', "Puma does not define the gaussian process builtins")
@on_inf_prim('none')
def testGPLogscore1():
  # Is this actually a valid test? The real solution to this problem
  # (and to the corresponding bug with unincorporate) is to wrap the
  # gp in a mem. This could be done automatically I suppose, or better
  # through a library function.

  raise SkipTest("GP logDensity is broken for multiple samples of the same input.")

  ripl = get_ripl()
  prep_ripl(ripl)

  prog = """
    [assume f (lambda (x) x)]
    [assume package ((allocate_gpmem) f zero sq_exp)]
    [assume f_emu (second package)]
  """
  ripl.execute_program(prog)

  ripl.predict('(f_emu (array 0 0))')
  ripl.get_global_logscore()

@broken_in('puma', "Puma does not define the gaussian process builtins")
@on_inf_prim('none')
def testGPAux():
  # Make sure the GP's aux is properly maintained.  It should be an
  # array of all pairs (x,y) such that the GP has been called with
  # input x and returned output y.

  ripl = get_ripl()
  prep_ripl(ripl)

  def check_firsts(stats, firsts):
    eq_(len(stats), len(firsts))
    eq_(set([xy[0] for xy in stats]), set(firsts))

  prog = """
    [assume f (lambda (x) x)]
    [assume package ((allocate_gpmem) f zero sq_exp)]
    [assume f_emu (second package)]
  """
  ripl.execute_program(prog)
  ripl.predict('(f_emu (array 1.0 3.0))')
  check_firsts(ripl.infer('(extract_stats f_emu)'), {1.0, 3.0})

  ripl.observe('(f_emu (array 5.0))', v.VentureArray(map(v.VentureNumber, [8.8])),
          label='obs')
  check_firsts(ripl.infer('(extract_stats f_emu)'), {1.0, 3.0, 5.0})

  ripl.forget('obs')
  check_firsts(ripl.infer('(extract_stats f_emu)'), {1.0, 3.0})



@statisticalTest
def testOneSample(seed):
  np_rng = npr.RandomState(seed)
  test_input = 1.4
  expect_mu = 4.6307
  expect_sig = 0.0027
  sigma = 2.1
  l = 1.8

  ripl = get_ripl()
  prep_ripl(ripl)
  ripl.set_mode("venture_script")
  ripl.assume("cov", """gp_cov_scale({scale_factor}, 
                            gp_cov_se({lengthscale}**2))""".format(scale_factor=sigma,
                            lengthscale=l))

  ripl.assume('f','(x) -> {x}');
  ripl.assume('package', 'allocate_gpmem()(f, zero, cov)')
  ripl.assume('f_emu', 'package[1]');

  ripl.observe("f_emu([1.3, -2.0, 0.0])", array([5.0,  2.3, 8.0]))


  # _gp_sample(..., test_input) should be normally distributed with
  # mean expect_mu.
  n = 4
  def sample():
    s =  ripl.sample("f_emu([1.4])")
    return s[0]
  samples = np.array([sample() for _ in xrange(n)])
  assert samples.shape == (n,)
  return reportKnownGaussian(expect_mu, np.sqrt(expect_sig), samples)

@statisticalTest
def testTwoSamples_low_covariance_f_emu(seed):
  ripl = get_ripl()
  prep_ripl(ripl)
  ripl.set_mode("venture_script")
  np_rng = npr.RandomState(seed)
  test_input = 1.4
  expect_mu = 4.6307
  expect_sig = 0.0027
  sigma = 2.1
  l = 1.8

  ripl = get_ripl()
  prep_ripl(ripl)
  ripl.set_mode("venture_script")
  ripl.assume("cov", """gp_cov_scale({scale_factor}, 
                            gp_cov_se({lengthscale}**2))""".format(scale_factor=sigma,
                            lengthscale=l))

  prog = """
    assume f  = (x) -> {x};
    assume package  = allocate_gpmem()(f, zero, cov);
    assume f_emu =  package[1];
  """
  ripl.execute_program(prog)

  ripl.observe("f_emu([1.3, -2.0, 0.0])", array([5.0,  2.3, 8.0]))

  # Fix n = 200, not higher even if we are doing a long-running
  # inference quality test, because we're trying to show that a
  # Pearson r^2 test of independence will fail to reject the null
  # hypothesis that the GP at two points with low covariance are
  # simply independent.  If we raised the number of samples
  # significantly higher, the test is likely to reject the null
  # hypothesis.
  # Edit (Ulli 2016-11-21): I don't see this picking up anything.
  n = 200
  lo_cov_x = []
  lo_cov_y = []
  for i in range(n):
    x, y = ripl.sample("f_emu([1.4, -20.0])")
    lo_cov_x.append(x)
    lo_cov_y.append(y)
  return reportPearsonIndependence(lo_cov_x, lo_cov_y)


@broken_in('puma', "Puma does not interpret the GP mean and covariance function objects.")
@stochasticTest
def test_gradients(seed):
  ripl = get_ripl(seed=seed)
  ripl.set_mode("venture_script")
  ripl.assume('mu_0', 'normal(0, 1)')
  ripl.assume('mean', 'gp_mean_const(mu_0)')
  ripl.assume('gs_expon_1',
    '( ) -> {-log_logistic(log_odds_uniform())}')
  ripl.assume('s2', 'gs_expon_1()')
  ripl.assume('alpha', 'gs_expon_1()')
  ripl.assume('cov', 'gp_cov_scale(s2,gp_cov_se(alpha))')
  ripl.assume('f','(x) -> {x}');
  ripl.assume('package', 'allocate_gpmem()(f, mean, cov)')
  ripl.assume('f_emu', 'package[1]');
  ripl.observe('f_emu([0])', array([1]))
  ripl.observe('f_emu([1])', array([2]))
  ripl.observe('f_emu([2])', array([4]))
  ripl.observe('f_emu([3])', array([8]))
  ripl.infer('grad_ascent(default, one, 0.1, 1, 1)')

