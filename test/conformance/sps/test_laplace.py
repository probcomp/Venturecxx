from venture.test.stats import statisticalTest, reportKnownContinuous
from venture.test.config import get_ripl, collectSamples, broken_in
from scipy.stats import laplace

@statisticalTest
@broken_in('puma', "Laplace distribution not implemented in Puma")
def testLaplace1():
  "Test that laplace distribution does what it should"
  ripl = get_ripl()
  # samples
  ripl.assume("a","(laplace -3 2)", label="pid")
  observed = collectSamples(ripl,"pid")
  # true CDF
  laplace_cdf = lambda x: laplace.cdf(x, -3, 2)
  return reportKnownContinuous(laplace_cdf, observed)
