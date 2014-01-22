from venture.test.stats import *
from testconfig import config

def testTrig1():
  "Simple test that verifies sin^2 + cos^2 = 1 as x varies"
  ripl = config["get_ripl"]()
  ripl.assume("sq","(lambda (x) (* x x))")
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("a","(sq (sin x))")
  ripl.assume("b","(sq (cos x))")
  ripl.predict("(+ a b)")
  for _ in range(10):
    ripl.infer(1)
    assert abs(ripl.report(5) - 1) < .001
  return reportPassage("TestTrig1")
