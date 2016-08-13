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
import scipy.stats

from venture.lite.utils import simulateLogGamma

from venture.test.config import default_num_samples
from venture.test.stats import reportKnownContinuous
from venture.test.stats import statisticalTest

@statisticalTest
def check_loggamma_ks(shape):
  np_rng = numpy.random.RandomState()         # XXX seed
  nsamples = default_num_samples()
  log_samples = [simulateLogGamma(shape, np_rng) for _ in xrange(nsamples)]
  samples = np.exp(np.array(log_samples))
  dist = scipy.stats.gamma(shape)
  return reportKnownContinuous(dist.cdf, samples)

def test_loggamma_ks():
  for shape in [.01, .1, 0.5, 1, 100, 1e6, 2, 10, 1e10]:
    yield check_loggamma_ks, shape
