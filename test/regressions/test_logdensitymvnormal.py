# Copyright (c) 2014 MIT Probabilistic Computing Project.
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
import numpy.linalg as npla
from scipy import stats
from nose.tools import assert_almost_equal

from venture.test.config import in_backend
from venture.lite.utils import logDensityMVNormal

@in_backend("none")
def testLogDensityMVNormal():
  x = np.array([1,2])
  mu = np.array([3,4])
  sigma = np.array(range(1,5)).reshape(2,2)
  sigma = sigma.dot(sigma.T)

  actual = logDensityMVNormal(x, mu, sigma)

  expect = -.5*np.dot(np.dot(x-mu, npla.inv(sigma)), np.transpose(x-mu)) \
           -.5*len(sigma)*np.log(2 * np.pi)-.5*np.log(abs(npla.det(sigma)))
  assert_almost_equal(actual, expect)

  if hasattr(stats, 'multivariate_normal'):
    expect = stats.multivariate_normal.logpdf(x, mu, sigma)
    assert_almost_equal(actual, expect)

