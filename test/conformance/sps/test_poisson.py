from venture.test.stats import statisticalTest, reportKnownMean
from venture.test.config import get_ripl, collectSamples

@statisticalTest
def testPoisson1():
  "Check that Poisson simulates and absorbs without crashing."
  ripl = get_ripl()

  ripl.assume("lambda","(gamma 1 1)",label="pid")
  ripl.predict("(poisson lambda)")

  predictions = collectSamples(ripl,"pid")
  return reportKnownMean(1,predictions)

@statisticalTest
def testPoisson2():
  "Check that Poisson simulates correctly."
  ripl = get_ripl()

  ripl.assume("lambda","5")
  ripl.predict("(poisson lambda)",label="pid")

  predictions = collectSamples(ripl,"pid")
  return reportKnownMean(5,predictions)
  
  

