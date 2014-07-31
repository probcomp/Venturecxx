from venture.test.config import get_ripl, on_inf_prim

@on_inf_prim("mh")
def testTrig1():
  "Simple test that verifies sin^2 + cos^2 = 1 as x varies"
  ripl = get_ripl()
  ripl.assume("sq","(lambda (x) (* x x))")
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("a","(sq (sin x))")
  ripl.assume("b","(sq (cos x))")
  ripl.predict("(+ a b)",label="pid")
  for _ in range(10):
    ripl.infer(1)
    assert abs(ripl.report("pid") - 1) < .001
