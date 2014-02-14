import math
import scipy.stats as stats
from nose import SkipTest

from venture.test.stats import statisticalTest, reportKnownContinuous, reportKnownMeanVariance, reportKnownDiscrete
from venture.test.config import get_ripl, collectSamples, collect_iid_samples

#@statisticalTest
def testBernoulli1():
  ripl = get_ripl()
  ripl.predict("(bernoulli 0.3)")
  # ripl.assume("x2", "(bernoulli 0.4)")
  # ripl.assume("x3", "(bernoulli 0.0)")
  # ripl.assume("x4", "(bernoulli 1.0)")
  # ripl.assume("x5", "(bernoulli)")  

  predictions = collectSamples(ripl,1)
#  ans = [(False, 0.3),(True, 0.7)]
#  return reportKnownDiscrete(ans, predictions)
