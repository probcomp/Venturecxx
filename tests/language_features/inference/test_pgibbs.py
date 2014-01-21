from venture.shortcuts import *
from stat_helpers import *
from test_globals import N, globalKernel

def RIPL(): return make_lite_church_prime_ripl()

# TODO N needs to be managed here more intelligently
def testPGibbsBlockingMHHMM1(N):
  """The point of this is that it should give reasonable results in very few transitions but with a large number of particles."""
  ripl = RIPL()

  ripl.assume("x0","(scope_include 0 0 (normal 0.0 1.0))")
  ripl.assume("x1","(scope_include 0 1 (normal x0 1.0))")
  ripl.assume("x2","(scope_include 0 2 (normal x1 1.0))")
  ripl.assume("x3","(scope_include 0 3 (normal x2 1.0))")
  ripl.assume("x4","(scope_include 0 4 (normal x3 1.0))")

  ripl.assume("y0","(normal x0 1.0)")
  ripl.assume("y1","(normal x1 1.0)")
  ripl.assume("y2","(normal x2 1.0)")
  ripl.assume("y3","(normal x3 1.0)")
  ripl.assume("y4","(normal x4 1.0)")

  ripl.observe("y0",1.0)
  ripl.observe("y1",2.0)
  ripl.observe("y2",3.0)
  ripl.observe("y3",4.0)
  ripl.observe("y4",5.0)
  ripl.predict("x4")

  predictions = collectSamplesWith(ripl,16,N,{"kernel":"pgibbs","transitions":10,"scope":0,"block":"ordered"})
  reportKnownMeanVariance("TestPGibbsBlockingMHHMM1", 390/89.0, 55/89.0, predictions)
  cdf = stats.norm(loc=390/89.0, scale=math.sqrt(55/89.0)).cdf
  return reportKnownContinuous("TestPGibbsBlockingMHHMM1", cdf, predictions, "N(4.382, 0.786)")
