from venture.test.stats import statisticalTest, reportKnownMean
from venture.test.config import get_ripl, collectSamples

@statisticalTest
def testGamma1():
  "Check that Gamma is parameterized correctly"
  ripl = get_ripl()

  ripl.assume("a","(gamma 10.0 10.0)")
  ripl.assume("b","(gamma 10.0 10.0)")
  ripl.predict("(gamma a b)")

  predictions = collectSamples(ripl,3)
  # Mean is E[(gamma 10 10)] * E[(inv_gamma 10 10)] = 1 * 10/9
  return reportKnownMean(10.0/9.0, predictions)

