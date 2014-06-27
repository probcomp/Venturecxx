from venture.test.stats import statisticalTest, reportKnownContinuous
from venture.test.config import get_ripl, collectSamples
from scipy.stats import invgamma

@statisticalTest
def testInvGamma1():
  "Check that Gamma is parameterized correctly"
  ripl = get_ripl()
  # samples
  ripl.assume("a","(inv_gamma 10.0 10.0)", label="pid")
  observed = collectSamples(ripl,"pid")
  # true CDF
  inv_gamma_cdf = lambda x: invgamma.cdf(x, a = 10, scale = 10)
  return reportKnownContinuous(inv_gamma_cdf, observed)
