# Copyright (c) 2013, 2014 MIT Probabilistic Computing Project.
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

import itertools
import numpy as np
from scipy.stats import norm

import venture.value.dicts as v
from venture.test.stats import statisticalTest, reportKnownContinuous
from venture.test.stats import reportSameContinuous
from venture.test.config import get_ripl, collectIidSamples
from venture.test.config import default_num_samples, ignore_inference_quality
from venture.test.config import gen_on_inf_prim

# This test suite targets
# - make_nig_normal(m,V,a,b)
# - make_uc_nig_normal(m,V,a,b)
# - make_suff_stat_normal(mu,sigma)

# The procedure for testing each of these functions is to:
# - Observe a random sample from a true underlying Normal(mu*, sigma*) dist.
# - Run posterior inference.
# - Simulate a random sample from the samplers.
# - Perform a KS-test under the null that Normal(mu*, sigma*) is the dist.

# Test against a variety of Normal distributions.
MU_TRUE_SMALL, VAR_TRUE_SMALL = 5, 2
MU_TRUE_MEDIUM, VAR_TRUE_MEDIUM = 40, 20
MU_TRUE_LARGE, VAR_TRUE_LARGE = 100, 50

# Sample 100 times from the true distribution.
DRAW_SAMPLE_SIZE = 100

# We will use emperical Bayes methods for the prior NIG hyperparams.

suff_stat_nig_normal = """(lambda (m V a b)
  (let ((variance (inv_gamma a b))
        (mean (normal m (sqrt (* V variance))))
        (stddev (sqrt variance)))
    (make_suff_stat_normal mean stddev)))"""

@gen_on_inf_prim("any")
def testRecoverNormalDist():
  for maker in ['make_nig_normal', 'make_uc_nig_normal', suff_stat_nig_normal]:
    for (true_mean, true_var) in itertools.product(
      [MU_TRUE_SMALL, MU_TRUE_MEDIUM, MU_TRUE_LARGE],
      [VAR_TRUE_SMALL, VAR_TRUE_MEDIUM, VAR_TRUE_LARGE]
      ):
        yield checkRecoverNormalDist, maker, true_mean, true_var

@statisticalTest
def checkRecoverNormalDist(maker, true_mean, true_var):
  if ignore_inference_quality():
    num_condition_samples = 2
  else:
    num_condition_samples = DRAW_SAMPLE_SIZE

  # Obtain samples from the true distribution.
  true_samples = norm.rvs(loc=true_mean, scale=np.sqrt(true_var),
                          size=num_condition_samples)

  # Emperical Bayes for hyperpriors. In theory we should converge regradless
  # of the hyperparameters. Should we test Griddy Gibbs? Slice sampling?
  m = np.random.uniform(low=min(true_samples), high=max(true_samples))
  V = np.random.uniform(high=1./12*(max(true_samples)-min(true_samples))**2)
  a = np.random.uniform(high=1./np.sqrt(np.var(true_samples))) + 1
  b = np.random.uniform(high=np.sqrt(np.var(true_samples)))

  # Set up the sampler.
  ripl = get_ripl()
  ripl.assume('f', '({} {} {} {} {})'.format(maker, m, V, a, b))

  # Observe.
  for s in true_samples:
    ripl.observe('(f)', s)

  # Collect samples from the posterior.
  ripl.predict('(f)',label='pid')
  predictive_samples = collectIidSamples(ripl, 'pid',
    num_samples=default_num_samples(5))

  return reportKnownContinuous(norm(loc=true_mean, scale=np.sqrt(true_var)).cdf,
                               predictive_samples,
                               "N(%s,%s)" % (true_mean, np.sqrt(true_var)))

native_nig_normal = """(lambda (m V a b)
  (let ((variance (inv_gamma a b))
        (mean (normal m (sqrt (* V variance))))
        (stddev (sqrt variance)))
    (lambda () (normal mean stddev))))"""

def extract_sample(maker, params, index):
  r = get_ripl()
  r.assume("maker", maker)
  expr = v.app(v.sym("list"), *[v.app(v.sym("made")) for _ in range(index+1)])
  def one_sample():
    r.assume("made", v.app(v.sym("maker"), *params))
    ans = r.sample(expr)[-1]
    r.forget("made")
    return ans
  results = [one_sample() for _ in range(default_num_samples(5))]
  return results

def extract_cross_sample(maker, params, index1, index2):
  r = get_ripl()
  r.assume("maker", maker)
  index = max(index1, index2)
  expr = v.app(v.sym("list"), *[v.app(v.sym("made")) for _ in range(index+1)])
  def one_sample():
    r.assume("made", v.app(v.sym("maker"), *params))
    vec = r.sample(expr)
    r.forget("made")
    return vec[index1] * vec[index2]
  results = [one_sample() for _ in range(default_num_samples(5))]
  return results

@statisticalTest
def checkSameMarginal(maker, params, index):
  return reportSameContinuous(extract_sample(native_nig_normal, params, index),
                              extract_sample(maker, params, index))

@statisticalTest
def checkSameCross(maker, params, index1, index2):
  return reportSameContinuous(extract_cross_sample(native_nig_normal, params, index1, index2),
                              extract_cross_sample(maker, params, index1, index2))

def testSameMarginal():
  for maker in ['make_nig_normal', 'make_uc_nig_normal', suff_stat_nig_normal]:
    for params in [(1.0, 1.0, 1.0, 1.0),
                   (2.0, 3.0, 4.0, 5.0)]:
      for index in [0, 10]:
        yield checkSameMarginal, maker, params, index
      for index1, index2 in [(1,2), (3,7)]:
        yield checkSameCross, maker, params, index1, index2
