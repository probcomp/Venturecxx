from venture.test.config import get_ripl

def testEq():
  assert get_ripl().predict("(eq 1 1)")

def testCompare():
  assert get_ripl().predict("(<= 1 1)")
  assert get_ripl().predict("(< 1 2)")
  assert not get_ripl().predict("(> 1 2)")
  assert not get_ripl().predict("(>= 1 2)")
