from venture.test.config import get_ripl, broken_in

def testUnevalConstantAndForget():
  """Check that unevaling a constant node does not produce a trace the
copying of which would be invalid."""
  ripl = get_ripl()
  ripl.predict("(if (flip) 0 1)", label="pid")
  ripl.infer(10)
  ripl.infer("(resample 5)")
  assert ripl.report("pid") in [0,1]
  ripl.forget("pid")
  ripl.infer("(resample 5)")

@broken_in('lite', "freeze is only implemented in Puma")
def testUnevalConstantAndFreeze():
  """Check that unevaling a constant node does not produce a trace the
copying of which would be invalid."""
  ripl = get_ripl()
  ripl.assume("foo", "(if (flip) 0 1)", label="pid")
  ripl.infer(10)
  ripl.infer("(resample 5)")
  assert ripl.report("pid") in [0,1]
  ripl.freeze("pid")
  ripl.infer("(resample 5)")

@broken_in('lite', "freeze is only implemented in Puma")
def testUnevalConstantAndFreezeWithObservations():
  """Check that unevaling a constant node does not produce an invalid
trace (even when transitions are rejected)."""
  ripl = get_ripl()
  ripl.assume("foo", "(if (flip) 0 1)", label="pid")
  ripl.observe("(normal foo 0.1)", 1)
  ripl.infer(40)
  ripl.infer("(resample 5)")
  assert ripl.report("pid") in [0,1]
  ripl.freeze("pid")
  ripl.infer("(resample 5)")
