from venture.test.config import get_ripl, gen_on_inf_prim

@gen_on_inf_prim("pgibbs")
def testBrushScopePGibbs():
  yield checkBrushScope, "pgibbs"

@gen_on_inf_prim("func_pgibbs")
def testBrushScopeFuncPGibbs():
  yield checkBrushScope, "func_pgibbs"

def checkBrushScope(operator):
  """Check that putting scope control in the brush doesn't cause
  particle Gibbs to crash."""
  ripl = get_ripl()
  ripl.assume("x1", "(tag (quote state) 0 (normal 1 1))")
  ripl.assume("t", "1") # This variable matters to get the block id into the brush.
  ripl.assume("x2", """
(if (> x1 1)
    (tag (quote state) t (normal 2 1))
    (tag (quote state) t (normal 0 1)))
""")
  ripl.infer("(%s state ordered 4 3)" % operator)
