from venture.test.config import get_ripl, collectSamples

def testBrushScope():
  yield checkBrushScope, True
  yield checkBrushScope, False

def checkBrushScope(mutate):
  """Check that putting scope control in the brush doesn't cause
  particle Gibbs to crash."""
  ripl = get_ripl()
  ripl.assume("x1", "(scope_include (quote state) 0 (normal 1 1))")
  ripl.assume("t", "1") # This variable matters to get the block id into the brush.
  ripl.assume("x2", """
(if (> x1 1)
    (scope_include (quote state) t (normal 2 1))
    (scope_include (quote state) t (normal 0 1)))
""")
  ripl.infer({"kernel":"pgibbs", "scope":"state", "block":"ordered", "transitions":3, "particles":4, "with_mutation":mutate})
