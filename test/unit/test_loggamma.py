# Copyright (c) 2016 MIT Probabilistic Computing Project.
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

import numpy as np
import numpy.random
import scipy.integrate
import scipy.stats

from nose import SkipTest

from venture.lite.utils import careful_exp
from venture.lite.utils import logDensityLogGamma
from venture.lite.utils import simulateLogGamma

from venture.test.config import default_num_samples
from venture.test.stats import reportKnownContinuous
from venture.test.stats import statisticalTest

def relerr(expected, actual):
  if expected == 0:
    return 0 if actual == 0 else 1
  else:
    return abs((actual - expected)/expected)

def check_loggamma_density_quad(shape):
  inf = float('inf')
  def pdf(x):
    return careful_exp(logDensityLogGamma(x, shape))
  one, esterr = scipy.integrate.quad(pdf, -inf, +inf)
  assert relerr(1, one) < esterr

def test_loggamma_density_quad():
  for shape in [.01, .1, .5, 1, 2, 10, 100, 1e6, 1e10]:
    if 1000 <= shape:
      raise SkipTest('scipy numerical integrator is unable to cope')
    yield check_loggamma_density_quad, shape

@statisticalTest
def check_loggamma_ks(shape, seed):
  np_rng = numpy.random.RandomState(seed)
  nsamples = default_num_samples()
  log_samples = [simulateLogGamma(shape, np_rng) for _ in xrange(nsamples)]
  samples = np.exp(np.array(log_samples))
  dist = scipy.stats.gamma(shape)
  return reportKnownContinuous(dist.cdf, samples)

def test_loggamma_ks():
  for shape in [.01, .1, .5, 1, 2, 10, 100, 1e6, 1e10]:
    yield check_loggamma_ks, shape
