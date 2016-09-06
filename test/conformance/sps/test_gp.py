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
def testGP1():
  ripl = get_ripl()
  prep_ripl(ripl)

  ripl.assume('gp', '(make_gp zero sq_exp)')
  ripl.sample('(gp (array 0))')
  ripl.sample('(gp (array 1))')
  ripl.sample('(gp (array 2))')

@broken_in('puma', "Puma does not define the gaussian process builtins")
@statisticalTest
def testGPMean1(seed):
  ripl = get_ripl(seed=seed)
  prep_ripl(ripl)

  ripl.assume('gp', '(make_gp zero sq_exp)')
  ripl.predict("(gp (array 0))",label="pid")

  predictions = collectSamples(ripl,"pid",num_samples=default_num_samples(2))
  xs = [p[0] for p in predictions]

  return reportKnownGaussian(0, 1, xs)

@broken_in('puma', "Puma does not define the gaussian process builtins")
@statisticalTest
def testGPMean2(seed):
  ripl = get_ripl(seed=seed)
  prep_ripl(ripl)

  ripl.assume('gp', '(make_gp zero sq_exp)')
  ripl.observe('(gp (array -1 1))', array([-1, 1]))

  ripl.predict("(gp (array 0))",label="pid")

  predictions = collectSamples(ripl,"pid")
  xs = [p[0] for p in predictions]

  # TODO: variance
  return reportKnownMean(0, xs)

@broken_in('puma', "Puma does not define the gaussian process builtins")
@on_inf_prim('mh')
def testHyperparameterInferenceSmoke():
  ripl = get_ripl()
  ripl.execute_program("""\
  [assume mean (gp_mean_const 0.)]
  [assume a (tag (quote hypers ) 0 (inv_gamma 2 5))]
  [assume l (tag (quote hypers ) 1 (inv_gamma 5 50))]
  [assume cov (gp_cov_scale a (gp_cov_se (* l l)))]
  [assume gp (make_gp mean cov)]
""")
  ripl.observe("(gp (array 1 2 3))", array([1.1, 2.2, 3.3]))
  ripl.infer("(mh (quote hypers) one 1)")

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

  ripl.assume('gp', '(exactly (make_gp zero sq_exp))')
  ripl.predict('(gp (array 0 0))')
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

  ripl.assume('gp', '(make_gp zero sq_exp)')
  ripl.predict('(gp (array 1.0 3.0))')
  check_firsts(ripl.infer('(extract_stats gp)'), {1.0, 3.0})

  ripl.observe('(gp (array 5.0))', v.VentureArray(map(v.VentureNumber, [8.8])),
          label='obs')
  check_firsts(ripl.infer('(extract_stats gp)'), {1.0, 3.0, 5.0})

  ripl.forget('obs')
  check_firsts(ripl.infer('(extract_stats gp)'), {1.0, 3.0})

@in_backend('none')
def testNormalParameters():
  obs_inputs = np.array([1.3, -2.0, 0.0])
  obs_outputs = np.array([5.0, 2.3, 8.0])
  test_inputs = np.array([1.4, -3.2])
  expect_mu = np.array([4.6307, -0.9046])
  expect_sig = np.array([[0.0027, -0.0231], [-0.0231, 1.1090]])
  sigma = 2.1
  l = 1.8
  observations = OrderedDict(zip(obs_inputs, obs_outputs))

  mean = gp.mean_const(0.)
  covariance = cov.scale(sigma**2, cov.se(l**2))
  actual_mu, actual_sig = gp._gp_mvnormal(mean, covariance, observations,
    test_inputs)
  np.testing.assert_almost_equal(actual_mu, expect_mu, decimal=4)
  np.testing.assert_almost_equal(actual_sig, expect_sig, decimal=4)

@in_backend('none')
@statisticalTest
def testOneSample(seed):
  np_rng = npr.RandomState(seed)
  obs_inputs  = np.array([1.3, -2.0, 0.0])
  obs_outputs = np.array([5.0,  2.3, 8.0])
  test_input = 1.4
  expect_mu = 4.6307
  expect_sig = 0.0027
  sigma = 2.1
  l = 1.8
  observations = OrderedDict(zip(obs_inputs, obs_outputs))

  mean = gp.mean_const(0.)
  covariance = cov.scale(sigma**2, cov.se(l**2))

  # _gp_sample(..., test_input) should be normally distributed with
  # mean expect_mu.
  n = default_num_samples(4)
  def sample():
    s = gp._gp_sample(mean, covariance, observations, [test_input], np_rng)
    return s[0]
  samples = np.array([sample() for _ in xrange(n)])
  assert samples.shape == (n,)
  return reportKnownGaussian(expect_mu, np.sqrt(expect_sig), samples)

@in_backend('none')
@statisticalTest
def testTwoSamples_low_covariance(seed):
  np_rng = npr.RandomState(seed)
  obs_inputs  = np.array([1.3, -2.0, 0.0])
  obs_outputs = np.array([5.0,  2.3, 8.0])
  in_lo_cov = np.array([1.4, -20.0])
  sigma = 2.1
  l = 1.8
  observations = OrderedDict(zip(obs_inputs, obs_outputs))

  mean = gp.mean_const(0.)
  covariance = cov.scale(sigma**2, cov.se(l**2))

  # Fix n = 200, not higher even if we are doing a long-running
  # inference quality test, because we're trying to show that a
  # Pearson r^2 test of independence will fail to reject the null
  # hypothesis that the GP at two points with low covariance are
  # simply independent.  If we raised the number of samples
  # significantly higher, the test is likely to reject the null
  # hypothesis.
  n = 200
  lo_cov_x = []
  lo_cov_y = []
  for i in range(n):
    x, y = gp._gp_sample(mean, covariance, observations, in_lo_cov, np_rng)
    lo_cov_x.append(x)
    lo_cov_y.append(y)
  return reportPearsonIndependence(lo_cov_x, lo_cov_y)

@stochasticTest
def test_gradients(seed):
  ripl = get_ripl(seed=seed)
  ripl.assume('mu_0', '(normal 0 1)')
  ripl.assume('mean', '(gp_mean_const mu_0)')
  ripl.assume('gs_expon_1',
    '(lambda () (- 0. (log_logistic (log_odds_uniform))))')
  ripl.assume('s', '(normal 0 1)')
  ripl.assume('alpha', '(gs_expon_1)')
  ripl.assume('cov', '(gp_cov_scale (* s s) (gp_cov_se alpha))')
  ripl.assume('gp', '(make_gp mean cov)')
  ripl.observe('(gp 0)', '1')
  ripl.observe('(gp 1)', '2')
  ripl.observe('(gp 2)', '4')
  ripl.observe('(gp 3)', '8')
  ripl.infer('(grad_ascent default one 0.1 10 10)')

@stochasticTest
def test_2d_isotropic(seed):
  ripl = get_ripl(seed=seed)
  ripl.assume('mu_0', '(normal 0 1)')
  ripl.assume('s', '(expon 1)')
  ripl.assume('l', '(expon 1)')
  ripl.assume('mean', '(gp_mean_const mu_0)')
  ripl.assume('cov', '(gp_cov_scale (* s s) (gp_cov_se (* l l)))')
  ripl.assume('gp', '(make_gp mean cov)')
  ripl.observe('(gp (array (array 0 1) (array 2 3)))', array([4, -4]))
  ripl.observe('(gp (array (array 5 6) (array 7 8)))', array([9, -9]))
  ripl.infer('(mh default one 1)')
  ripl.sample('(gp (array (array 2 3) (array 5 7)))')

@stochasticTest
def test_2d_linear(seed):
  ripl = get_ripl(seed=seed)
  ripl.assume('mu_0', '(normal 0 1)')
  ripl.assume('s', '(expon 1)')
  ripl.assume('off_set_1', '(expon 1)')
  ripl.assume('off_set_2', '(expon 1)')
  ripl.assume('mean', '(gp_mean_const mu_0)')
  ripl.assume('cov', '(gp_cov_scale (* s s) (gp_cov_linear (array (* off_set_1  off_set_1 )(* off_set_2 off_set_2 ))))')
  ripl.assume('gp', '(make_gp mean cov)')
  ripl.observe('(gp (array (array 0 1) (array 2 3)))', array([4, -4]))
  ripl.observe('(gp (array (array 5 6) (array 7 8)))', array([9, -9]))
  ripl.infer('(mh default one 1)')
  ripl.sample('(gp (array (array 2 3) (array 5 7)))')

@stochasticTest
def test_2d_gradients(seed):
  ripl = get_ripl(seed=seed)
  ripl.assume('gs_expon_1',
    '(lambda () (- 0. (log_logistic (log_odds_uniform))))')
  ripl.assume('mu_0', '(normal 0 1)')
  ripl.assume('s', '(gs_expon_1)')
  ripl.assume('l', '(gs_expon_1)')
  ripl.assume('mean', '(gp_mean_const mu_0)')
  ripl.assume('cov', '(gp_cov_scale (* s s) (gp_cov_se (* l l)))')
  ripl.assume('gp', '(make_gp mean cov)')
  ripl.observe('(gp (array (array 0 1) (array 2 3)))', array([4, -4]))
  ripl.observe('(gp (array (array 5 6) (array 7 8)))', array([9, -9]))
  ripl.infer('(grad_ascent default one 0.1 10 10)')
  ripl.sample('(gp (array (array 2 3) (array 5 7)))')

@stochasticTest
def test_bump_gradient(seed):
  ripl = get_ripl(seed=seed)
  ripl.assume('gs_expon_1',
    '(lambda () (- 0. (log_logistic (log_odds_uniform))))')
  ripl.assume('mu_0', '(normal 0 1)')
  ripl.assume('s', '(gs_expon_1)')
  ripl.assume('l', '(gs_expon_1)')
  ripl.assume('t', '1')
  ripl.assume('z', '1')
  ripl.assume('mean', '(gp_mean_const mu_0)')
  ripl.assume('cov', '''
    (gp_cov_sum
     (gp_cov_scale (* s s) (gp_cov_se (* l l)))
     (gp_cov_bump t z))
  ''')
  ripl.assume('gp', '(make_gp mean cov)')
  ripl.observe('(gp (array (array 0 1) (array 2 3)))', array([4, -4]))
  ripl.observe('(gp (array (array 5 6) (array 7 8)))', array([9, -9]))
  ripl.infer('(grad_ascent default one 0.1 10 10)')
  ripl.sample('(gp (array (array 2 3) (array 5 7)))')
