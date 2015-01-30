from venture.test.stats import statisticalTest, reportKnownContinuous
from venture.test.config import get_ripl, collectSamples
from scipy.stats import expon

@statisticalTest
def testExpon1():
  "Check that exponential distribution is parameterized correclty"
  ripl = get_ripl()
  ripl.assume("a", "(expon 4.0)", label = "pid")
  observed = collectSamples(ripl, "pid")
  expon_cdf = lambda x: expon.cdf(x, scale = 1. / 4)
  return reportKnownContinuous(expon_cdf, observed)
