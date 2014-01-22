from venture.test.stats import *
from testconfig import config

def testGamma1():
  "Check that Gamma is parameterized correctly"
  ripl = config["get_ripl"]()

  ripl.assume("a","(gamma 10.0 10.0)")
  ripl.assume("b","(gamma 10.0 10.0)")
  ripl.predict("(gamma a b)")

  predictions = collectSamples(ripl,3)
  # TODO What, actually, is the mean of (gamma (gamma 10 10) (gamma 10 10))?
  # It's pretty clear that it's not 1.
  return reportKnownMean("TestGamma1", 10/9.0, predictions)

