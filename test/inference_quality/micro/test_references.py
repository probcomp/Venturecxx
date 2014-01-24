from venture.test.stats import *
from testconfig import config


@statisticalTest
def testReferences1():
  """Checks that the program runs without crashing. At some point, this program caused CXX to fire an assert.  When the (flip) had a 0.0 or 1.0 it didn't fail."""
  ripl = config["get_ripl"]()
  ripl.assume("draw_type0", "(make_crp 1.0)")
  ripl.assume("draw_type1", "(if (flip) draw_type0 (lambda () atom<1>))")
  ripl.assume("draw_type2", "(make_dir_mult (simplex 1.0 1.0))")
  ripl.assume("class", "(if (flip) (lambda (name) (draw_type1)) (lambda (name) (draw_type2)))")
  ripl.predict("(class 1)")
  ripl.predict("(flip)")

  predictions = collectSamples(ripl,6)
  ans = [(True,0.5), (False,0.5)]
  return reportKnownDiscrete("TestReferences1", ans, predictions)


@statisticalTest
def testReferences2():
  "Simpler version of the old bug testReferences1() tries to trigger"
  ripl = config["get_ripl"]()
  ripl.assume("f", "(if (flip 0.5) (make_dir_mult (simplex 1.0 1.0)) (lambda () atom<1>))")
  ripl.predict("(f)")

  predictions = collectSamples(ripl,2)
  ans = [(True,0.75), (False,0.25)]
  return reportKnownDiscrete("TestReferences2", ans, predictions)
