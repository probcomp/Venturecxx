def testTrig1():
  "Simple test that verifies sin^2 + cos^2 = 1 as x varies"
  N = config["num_samples"]
  ripl = config["get_ripl"]()
  ripl.assume("sq","(lambda (x) (* x x))")
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("a","(sq (sin x))")
  ripl.assume("b","(sq (cos x))")
  ripl.predict("(+ a b)")
  for i in range(N):
    ripl.infer(1)
    assert abs(ripl.report(5) - 1) < .001
  return reportPassage("TestTrig1")
