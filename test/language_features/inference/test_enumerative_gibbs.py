from venture.test.stats import *

# TODO N needs to be managed here more intelligently
@statisticalTest
def testEnumerativeGibbsBasic1():
  """Basic sanity test"""
  ripl = get_ripl()
  ripl.predict("(bernoulli)",label="pid")

  predictions = collectSamples(ripl,"pid",None,{"kernel":"gibbs"})
  ans = [(True,.5),(False,.5)]
  return reportKnownDiscrete("TestEnumerativeGibbsBasic1", ans, predictions)

@statisticalTest
def testEnumerativeGibbsXOR1():
  """Tests that an XOR chain mixes with enumerative gibbs.
     Note that with RESET=True, this will seem to mix with MH.
     The next test accounts for that."""
  ripl = get_ripl()

  ripl.assume("x","(scope_include 0 0 (bernoulli 0.001))",label="pid")
  ripl.assume("y","(scope_include 0 0 (bernoulli 0.001))")
  ripl.assume("noisy_true","(lambda (pred noise) (flip (if pred 1.0 noise)))")
  ripl.observe("(noisy_true (= (+ x y) 1) .001)","true")
  predictions = collectSamples(ripl,"pid",None,{"kernel":"gibbs","scope":0,"block":0})
  ans = [(True,.5),(False,.5)]
  return reportKnownDiscrete("TestEnumerativeGibbsXOR1", ans, predictions)

@statisticalTest
def testEnumerativeGibbsXOR2():
  """Tests that an XOR chain mixes with enumerative gibbs."""
  ripl = get_ripl()

  ripl.assume("x","(scope_include 0 0 (bernoulli 0.0015))",label="pid")
  ripl.assume("y","(scope_include 0 0 (bernoulli 0.0005))")
  ripl.assume("noisy_true","(lambda (pred noise) (flip (if pred 1.0 noise)))")
  ripl.observe("(noisy_true (= (+ x y) 1) .001)","true")
  predictions = collectSamples(ripl,"pid",None,{"kernel":"gibbs","scope":0,"block":0})
  ans = [(True,.75),(False,.25)]
  return reportKnownDiscrete("TestEnumerativeGibbsXOR2", ans, predictions)
