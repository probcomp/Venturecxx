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

from nose import SkipTest

from scipy.stats import poisson
from venture.test.stats import statisticalTest, reportKernelTwoSampleTest
from venture.test.config import get_ripl, collectIidSamples, default_num_samples, ignore_inference_quality, rejectionSampling, gen_on_inf_prim

# This test suite targets
# - make_gamma_poisson(a,b)
# - make_uc_gamma_poisson(a,b)
# - make_suff_stat_poisson(mu)

# The procedure for testing each of these functions is to:
# - Observe a random sample from a true underlying Poisson(mu*) distribution.
# - Run posterior inference.
# - Simulate a random sample from the samplers.
# - Perform Chi2 Goodness-of-Fit test on generated samples against Poisson(mu*).

# The tests explore various combinations of mu*, gamma hyperparameters, and
# observed sample size. It is expected that, when the prior on mu is far from
# the true mu*, a larger sample size will be requried for the likelihood to
# dominate the prior. In theory the Bayesian posterior will converge to a delta
# on the true mu* if prior density on mu* is non-zero. There are things to be
# said about convergence rate.


# Use a variety of priors. SMALL and LARGE are mostly informative, WIDE is vague.
PRIOR_SMALL = (1,1)
PRIOR_WIDE = (2, 0.1)
PRIOR_LARGE = (60,1)

# Vary the true Poisson distribution mean.
MU_TRUE_SMALL = 5
MU_TRUE_MEDIUM = 40
MU_TRUE_LARGE = 100

# Sample 200 times from the true distribution.
DRAW_SAMPLE_SIZE = 200

@gen_on_inf_prim("any")
def testRecoverPoissonDist():
  for maker in ['make_gamma_poisson', 'make_uc_gamma_poisson', 'make_suff_stat_poisson']:
    for gamma_hypers, mu_true in [
      (PRIOR_SMALL, MU_TRUE_SMALL),
      (PRIOR_SMALL, MU_TRUE_MEDIUM),
      (PRIOR_WIDE, MU_TRUE_SMALL),
      (PRIOR_WIDE, MU_TRUE_MEDIUM),
      (PRIOR_WIDE, MU_TRUE_LARGE),
      (PRIOR_LARGE, MU_TRUE_MEDIUM),
      (PRIOR_LARGE, MU_TRUE_LARGE),
      ]:
        yield checkRecoverPoissonDist, maker, gamma_hypers, mu_true

@statisticalTest
def checkRecoverPoissonDist(maker, gamma_hypers, mu_true):
  # Set up the sampler.
  ripl = get_ripl()
  # Conjugate models initialized directly.
  if maker in ['make_gamma_poisson', 'make_uc_gamma_poisson']:
    ripl.assume('f', '({} {} {})'.format(maker,
      gamma_hypers[0], gamma_hypers[1]))
  # Set up a conjugate prior for the vanilla Poisson. Test an arbitrary prior?
  elif maker in ['make_suff_stat_poisson']:
    if rejectionSampling() and \
       not (gamma_hypers == PRIOR_WIDE and \
            mu_true < 10):
      raise SkipTest("Rejection sampling is too slow for make_suff_stat_poisson")
    ripl.assume('mu', '(gamma {} {})'.format(gamma_hypers[0], gamma_hypers[1]))
    ripl.assume('f', '({} mu)'.format(maker))
  else:
    raise Exception('Unknown maker {}'.format(maker))

  if ignore_inference_quality():
    num_condition_samples = 2
  else:
    num_condition_samples = DRAW_SAMPLE_SIZE

  # Obtain samples from the true distribution.
  true_samples = poisson.rvs(mu_true, size = num_condition_samples)

  # Observe.
  for s in true_samples:
    ripl.observe('(f)', s)

  # Collect samples from the posterior.
  ripl.predict('(f)',label='pid')
  predictive_samples = collectIidSamples(ripl, 'pid',
    num_samples=default_num_samples())

  # Resample from the true distribution to test the posterior.
  test_samples = poisson.rvs(mu_true, size = num_condition_samples)

  # Perform non-parametric two-sample test.
  return reportKernelTwoSampleTest(
    [[r] for r in test_samples],
    [[r] for r in predictive_samples],
    2 if ignore_inference_quality() else None)
