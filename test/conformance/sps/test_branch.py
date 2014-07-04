import scipy.stats as stats
from venture.test.config import get_ripl, collectSamples, skipWhenRejectionSampling
from venture.test.stats import statisticalTest, reportKnownContinuous

@skipWhenRejectionSampling("Rejection sampling doesn't work when resimulations of unknown code are observed")
@statisticalTest
def testBranch1():
  ripl = get_ripl()

  ripl.assume("p","(uniform_continuous 0.0 1.0)",label="pid")
  ripl.assume("x","""
(branch (bernoulli p)
  (quote (normal 10.0 1.0))
  (quote (normal 0.0 1.0)))
""")
  ripl.observe("x",11.0)
  predictions = collectSamples(ripl,"pid")
  cdf = stats.beta(2,1).cdf # The observation nearly guarantees the first branch is taken
  return reportKnownContinuous(cdf, predictions, "approximately beta(2,1)")
