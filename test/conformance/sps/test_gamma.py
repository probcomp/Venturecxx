from venture.test.stats import statisticalTest, reportKnownContinuous
from venture.test.config import get_ripl, collectSamples
from scipy.stats import gamma

@statisticalTest
def testGamma1():
  "Check that Gamma is parameterized correctly"
  ripl = get_ripl()
  # samples
  ripl.assume("a","(gamma 10.0 10.0)",label ="pid")
  observed = collectSamples(ripl,"pid")
  # true CDF
  gamma_cdf = lambda x: gamma.cdf(x, a = 10, scale = 1 / 10.)
  return reportKnownContinuous(gamma_cdf, observed)
