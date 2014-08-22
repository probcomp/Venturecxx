import numpy as np
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

