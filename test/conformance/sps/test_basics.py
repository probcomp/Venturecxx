from venture.test.config import get_ripl

def testEq():
  assert get_ripl().predict("(eq 1 1)")
