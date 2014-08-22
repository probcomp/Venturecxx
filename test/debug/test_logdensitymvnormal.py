import numpy as np
from scipy import stats
from nose.tools import assert_almost_equal

from venture.test.config import in_backend, broken_in
from venture.lite.utils import logDensityMVNormal

@broken_in('lite', "Bug in computing the log density")
@in_backend("lite")
def testLogDensityMVNormal():
  x = np.array([1,2])
  mu = np.array([3,4])
  sigma = np.array(range(1,5)).reshape(2,2)
  sigma = sigma.dot(sigma.T)

  expect = stats.multivariate_normal.logpdf(x, mu, sigma)

  # The number 2 is missing in the buggy code.
  correct = -.5*np.dot(np.dot(x-mu, npla.inv(sigma)), np.transpose(x-mu)) \
            -.5*len(sigma)*np.log(2 * np.pi)-.5*np.log(abs(npla.det(sigma)))

  assert_almost_equal(correct, expect)

  actual = logDensityMVNormal(x, mu, sigma)

  assert_almost_equal(actual, expect)

