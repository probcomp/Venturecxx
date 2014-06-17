import scipy.stats as stats
from venture.test.stats import statisticalTest, reportKnownContinuous
from venture.test.config import get_ripl, default_num_samples

@statisticalTest
def testPeekSmoke():
  ripl = get_ripl()
  ripl.assume("x", "(normal 0 1)")
  predictions = ripl.infer("(cycle ((mh default one 1) (peek x)) %s)" % default_num_samples())['x']
  cdf = stats.norm(loc=0.0, scale=1.0).cdf
  return reportKnownContinuous(cdf, predictions, "N(0,1)")
