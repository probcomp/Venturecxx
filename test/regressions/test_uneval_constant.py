from testconfig import config
from nose import SkipTest
from venture.test.config import get_ripl

def testUnevalConstantAndForget():
  """Check that unevaling a constant node does not produce a trace the
copying of which would be invalid."""
  ripl = get_ripl()
  ripl.predict("(if (flip) 0 1)")
  ripl.infer(10)
  ripl.infer("(resample 5)")
  assert ripl.report(1) in [0,1]
  ripl.forget(1)
  ripl.infer("(resample 5)")

def testUnevalConstantAndFreeze():
  """Check that unevaling a constant node does not produce a trace the
copying of which would be invalid."""
  if config["get_ripl"] != "puma":
    raise SkipTest("freeze only implemented in Puma")
  ripl = get_ripl()
  ripl.assume("foo", "(if (flip) 0 1)")
  ripl.infer(10)
  ripl.infer("(resample 5)")
  assert ripl.report(1) in [0,1]
  ripl.freeze(1)
  ripl.infer("(resample 5)")

def testUnevalConstantAndFreezeWithObservations():
  """Check that unevaling a constant node does not produce an invalid
trace (even when transitions are rejected)."""
  if config["get_ripl"] != "puma":
    raise SkipTest("freeze only implemented in Puma")
  ripl = get_ripl()
  ripl.assume("foo", "(if (flip) 0 1)")
  ripl.observe("(normal foo 0.1)", 1)
  ripl.infer(40)
  ripl.infer("(resample 5)")
  assert ripl.report(1) in [0,1]
  ripl.freeze(1)
  ripl.infer("(resample 5)")
