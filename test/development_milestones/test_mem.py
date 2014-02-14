from venture.test.config import get_ripl, collectSamples
from nose.tools import assert_equal

def testMem1():
  ripl = get_ripl()
  ripl.assume('f', '(mem flip)')
  flip1 = ripl.predict('(f)')
  flip2 = ripl.predict('(f)')
  assertEqual(flip1, flip2)
