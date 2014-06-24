import scipy.stats as stats
from nose import SkipTest
from venture.test.config import get_ripl, collectSamples, defaultKernel
from venture.test.stats import statisticalTest, reportKnownContinuous

@statisticalTest
def testBranch1():
  if defaultKernel() == "rejection":
    raise SkipTest("Rejection sampling doesn't work when resimulations of unknown code are observed")
  ripl = get_ripl()

  ripl.assume("p","(uniform_continuous 0.0 1.0)",label='prediction')
  ripl.assume("x","""
(branch (bernoulli p)
  (quote (normal 10.0 1.0))
  (quote (normal 0.0 1.0)))
""")
  ripl.observe("x",11.0)
  predictions = collectSamples(ripl,'prediction')
  cdf = stats.beta(2,1).cdf # The observation nearly guarantees the first branch is taken
  return reportKnownContinuous(cdf, predictions, "approximately beta(2,1)")
