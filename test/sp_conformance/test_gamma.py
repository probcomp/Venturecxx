from venture.shortcuts import *
from stat_helpers import *
from test_globals import N, globalKernel

def RIPL(): return make_lite_church_prime_ripl()


def testGamma1(N):
  "Check that Gamma is parameterized correctly"
  ripl = RIPL()
  ripl.assume("a","(gamma 10.0 10.0)")
  ripl.assume("b","(gamma 10.0 10.0)")
  ripl.predict("(gamma a b)")

  predictions = collectSamples(ripl,3,N)
  # TODO What, actually, is the mean of (gamma (gamma 10 10) (gamma 10 10))?
  # It's pretty clear that it's not 1.
  return reportKnownMean("TestGamma1", 10/9.0, predictions)

