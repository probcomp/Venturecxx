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
import numpy.linalg as la
import scipy.stats as stats

from venture.test.config import broken_in
from venture.test.config import collectSamples
from venture.test.config import default_num_samples
from venture.test.config import get_ripl
from venture.test.stats import reportKnownGaussian
from venture.test.stats import reportKnownMean
from venture.test.stats import statisticalTest
import venture.lite.covariance as cov
import venture.lite.gp as gp
import venture.lite.value as v

def prep_ripl(ripl):
  ripl.assume('zero', "(gp_mean_const 0.)")
  ripl.assume('sq_exp', "(gp_cov_se 1.)")

def array(xs):
  return v.VentureArrayUnboxed(np.array(xs), gp.xType)

@broken_in('puma', "Puma does not define the gaussian process builtins")
def testGP1():
  ripl = get_ripl()
  prep_ripl(ripl)

  ripl.assume('gp', '(make_gp zero sq_exp)')
  ripl.sample('(gp (array 0))')
  ripl.sample('(gp (array 1))')
  ripl.sample('(gp (array 2))')

@broken_in('puma', "Puma does not define the gaussian process builtins")
@statisticalTest
def testGPMean1():
  ripl = get_ripl()
  prep_ripl(ripl)

  ripl.assume('gp', '(make_gp zero sq_exp)')
  ripl.predict("(gp (array 0))",label="pid")

  predictions = collectSamples(ripl,"pid",num_samples=default_num_samples(2))
  xs = [p[0] for p in predictions]

  return reportKnownGaussian(0, 1, xs)

@broken_in('puma', "Puma does not define the gaussian process builtins")
@statisticalTest
def testGPMean2():
  ripl = get_ripl()
  prep_ripl(ripl)

  ripl.assume('gp', '(make_gp zero sq_exp)')
  ripl.observe('(gp (array -1 1))', array([-1, 1]))

  ripl.predict("(gp (array 0))",label="pid")

  predictions = collectSamples(ripl,"pid")
  xs = [p[0] for p in predictions]

  # TODO: variance
  return reportKnownMean(0, xs)

@broken_in('puma', "Puma does not define the gaussian process builtins")
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
def testGPLogscore1():
  """Is this actually a valid test? The real solution to this problem
  (and to the corresponding bug with unincorporate) is to wrap the gp
  in a mem. This could be done automatically I suppose, or better
  through a library function."""

  raise SkipTest("GP logDensity is broken for multiple samples of the same input.")

  ripl = get_ripl()
  prep_ripl(ripl)

  ripl.assume('gp', '(exactly (make_gp zero sq_exp))')
  ripl.predict('(gp (array 0 0))')
  ripl.get_global_logscore()

@broken_in('puma', "Puma does not define the gaussian process builtins")
def testGPAux():
  """Make sure the GP's aux is properly maintained.  It should be an array of
  all pairs (x,y) such that the GP has been called with input x and returned
  output y."""

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

@broken_in('puma', "Puma does not define the gaussian process builtins")
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
  gp_class = gp.GP(mean, covariance, observations)
  actual_mu, actual_sig = gp_class.getNormal(test_inputs)
  np.testing.assert_almost_equal(actual_mu, expect_mu, decimal=4)
  np.testing.assert_almost_equal(actual_sig, expect_sig, decimal=4)

@broken_in('puma', "Puma does not define the gaussian process builtins")
@statisticalTest
def testOneSample():
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
  gp_class = gp.GP(mean, covariance, observations)

  # gp_class.sample(test_input) should be normally distributed with
  # mean expect_mu.
  n = 200
  samples = np.array([gp_class.sample([test_input])[0] for _ in xrange(n)])
  assert samples.shape == (n,)
  return reportKnownGaussian(expect_mu, expect_sig, samples)
