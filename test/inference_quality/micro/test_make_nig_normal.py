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
from venture.test.stats import statisticalTest, reportKnownContinuous
from venture.test.config import get_ripl, collectIidSamples, default_num_samples, ignore_inference_quality

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
    num_samples=default_num_samples() * 5)

  return reportKnownContinuous(norm(loc=true_mean, scale=np.sqrt(true_var)).cdf,
                               predictive_samples,
                               "N(%s,%s)" % (true_mean, np.sqrt(true_var)))
