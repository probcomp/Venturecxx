from venture.test.config import get_ripl, collectSamples
from nose.tools import assert_equal

def testNormal1():
  ripl = get_ripl()
  ripl.predict("(normal 0 1)")
