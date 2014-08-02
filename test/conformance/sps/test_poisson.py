import scipy.stats
from venture.test.stats import statisticalTest, reportKnownMean, reportKnownContinuous
from venture.test.config import get_ripl, collectSamples

@statisticalTest
def testPoisson1():
  "Check that Poisson simulates and absorbs without crashing."
  ripl = get_ripl()

  ripl.assume("lambda","(gamma 1 1)",label="pid")
  #ripl.predict("(poisson lambda)")

  predictions = collectSamples(ripl,"pid")
  return reportKnownContinuous(scipy.stats.gamma(1, scale=1/1.0).cdf,predictions,"(gamma 1 1)")

@statisticalTest
def testPoisson2():
  "Check that Poisson simulates correctly."
  ripl = get_ripl()

  ripl.assume("lambda","5")
  ripl.predict("(poisson lambda)",label="pid")

  predictions = collectSamples(ripl,"pid")
  return reportKnownMean(5,predictions)
  
