from venture.test.stats import statisticalTest, reportKnownDiscrete
from venture.test.config import get_ripl, collectSamples
from nose import SkipTest
from testconfig import config

@statisticalTest
def testEnumerativeGibbsBasic1():
  """Basic sanity test"""
  ripl = get_ripl()
  ripl.predict("(bernoulli)",label="pid")

  predictions = collectSamples(ripl,"pid",infer={"kernel":"gibbs"})
  ans = [(True,.5),(False,.5)]
  return reportKnownDiscrete(ans, predictions)

def testEnumerativeGibbsGotcha():
  """Enumeration should not break on things that look like they're in the support but aren't"""
  ripl = get_ripl()
  ripl.predict("(bernoulli 1)")
  ripl.predict("(bernoulli 0)")
  ripl.infer({"kernel":"gibbs"})
  ripl.infer({"kernel":"gibbs", "scope":"default", "block":"all"})

@statisticalTest
def testEnumerativeGibbsXOR1():
  """Tests that an XOR chain mixes with enumerative gibbs.
     Note that with RESET=True, this will seem to mix with MH.
     The next test accounts for that."""
  ripl = get_ripl()

  ripl.assume("x","(scope_include 0 0 (bernoulli 0.001))",label="pid")
  ripl.assume("y","(scope_include 0 0 (bernoulli 0.001))")
  ripl.assume("noisy_true","(lambda (pred noise) (flip (if pred 1.0 noise)))")
  ripl.observe("(noisy_true (= (+ x y) 1) .000001)","true")
  predictions = collectSamples(ripl,"pid",infer={"kernel":"gibbs","scope":0,"block":0})
  ans = [(True,.5),(False,.5)]
  return reportKnownDiscrete(ans, predictions)

@statisticalTest
def testEnumerativeGibbsXOR2():
  """Tests that an XOR chain mixes with enumerative gibbs."""
  ripl = get_ripl()

  ripl.assume("x","(scope_include 0 0 (bernoulli 0.0015))",label="pid")
  ripl.assume("y","(scope_include 0 0 (bernoulli 0.0005))")
  ripl.assume("noisy_true","(lambda (pred noise) (flip (if pred 1.0 noise)))")
  ripl.observe("(noisy_true (= (+ x y) 1) .000001)","true")
  predictions = collectSamples(ripl,"pid",infer={"kernel":"gibbs","scope":0,"block":0})
  ans = [(True,.75),(False,.25)]
  return reportKnownDiscrete(ans, predictions)

@statisticalTest
def testEnumerativeGibbsXOR3():
  """A regression catching a mysterious math domain error."""
  ripl = get_ripl()

  ripl.assume("x","(scope_include 0 0 (bernoulli 0.0015))",label="pid")
  ripl.assume("y","(scope_include 0 0 (bernoulli 0.0005))")
  ripl.assume("noisy_true","(lambda (pred noise) (scope_include 0 0 (flip (if pred 1.0 noise))))")
  # This predict is the different between this test and
  # testEnumerativeGibbsXOR2, and currently causes a mystery math
  # domain error.

  ripl.predict("(noisy_true (= (+ x y) 1) .000001)")
  ripl.observe("(noisy_true (= (+ x y) 1) .000001)","true")
  predictions = collectSamples(ripl,"pid",infer={"kernel":"gibbs","scope":0,"block":0})
  ans = [(True,.75),(False,.25)]
  return reportKnownDiscrete(ans, predictions)
