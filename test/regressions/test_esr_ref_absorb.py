from venture.test.stats import *
from nose.tools import *
from nose import SkipTest

@statisticalTest
def testESRRefAbsorb1():
  """
  This test ensures that an ESRRefOutputPSP does not absorb when its RequestPSP
  might change.
  """
  ripl = get_ripl()
  ripl.predict("(branch (flip 0.7) 1 0)",label="pid")
  predictions = collectSamples(ripl,"pid")
  ans = [(1, .7), (0, .3)]
  return reportKnownDiscrete("TestESRRefAbsorb1", ans, predictions)
