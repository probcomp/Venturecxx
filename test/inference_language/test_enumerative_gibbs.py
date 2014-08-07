from venture.test.stats import statisticalTest, reportKnownDiscrete
from venture.test.config import get_ripl, collectSamples, default_num_transitions_per_sample, gen_on_inf_prim, on_inf_prim

@gen_on_inf_prim("gibbs")
def testEnumerativeGibbsBasic1():
  yield checkEnumerativeGibbsBasic1, "false"
  yield checkEnumerativeGibbsBasic1, "true"

@statisticalTest
def checkEnumerativeGibbsBasic1(in_parallel):
  """Basic sanity test"""
  ripl = get_ripl()
  ripl.predict("(bernoulli)",label="pid")
  infer = "(gibbs default one %s %s)" % (default_num_transitions_per_sample(), in_parallel)

  predictions = collectSamples(ripl,"pid",infer=infer)
  ans = [(True,.5),(False,.5)]
  return reportKnownDiscrete(ans, predictions)

@gen_on_inf_prim("gibbs")
def testEnumerativeGibbsBasic2():
  yield checkEnumerativeGibbsBasic2, "false"
  yield checkEnumerativeGibbsBasic2, "true"

@statisticalTest
def checkEnumerativeGibbsBasic2(in_parallel):
  """Basic sanity test"""
  ripl = get_ripl()
  ripl.assume("x","(flip 0.1)",label="pid")
  infer = "(gibbs default one %s %s)" % (default_num_transitions_per_sample(), in_parallel)
  predictions = collectSamples(ripl,"pid",infer=infer)
  ans = [(False,.9),(True,.1)]
  return reportKnownDiscrete(ans, predictions)

@gen_on_inf_prim("gibbs")
def testEnumerativeGibbsGotcha():
  yield checkEnumerativeGibbsGotcha, "false"
  yield checkEnumerativeGibbsGotcha, "true"

def checkEnumerativeGibbsGotcha(in_parallel):
  """Enumeration should not break on things that look like they're in the support but aren't"""
  ripl = get_ripl()
  ripl.predict("(bernoulli 1)")
  ripl.predict("(bernoulli 0)")
  ripl.infer("(gibbs default one 1 %s)" % in_parallel)
  ripl.infer("(gibbs default all 1 %s)" % in_parallel)

@statisticalTest
@on_inf_prim("gibbs")
def testEnumerativeGibbsBoostThrashExact():
  """Enumerating two choices with the same posterior probability should not thrash"""
  ripl = get_ripl()
  ripl.assume("x","(flip 0.1)",label="pid")
  ripl.observe("(flip (if x .9 .1))","true")
  predictions = collectSamples(ripl,"pid",infer="(gibbs default one 1)")
  ans = [(False,.5),(True,.5)]
  return reportKnownDiscrete(ans, predictions)

@gen_on_inf_prim("gibbs")
def testEnumerativeGibbsBoostThrashClose():
  yield checkEnumerativeGibbsBoostThrashClose, "false"
  yield checkEnumerativeGibbsBoostThrashClose, "true"

@statisticalTest
def checkEnumerativeGibbsBoostThrashClose(in_parallel):
  """Enumerating two choices with almost the same posterior probability should mix well"""
  ripl = get_ripl()
  ripl.assume("x","(flip 0.1)",label="pid")
  ripl.observe("(flip (if x .91 .09))","true")
  infer = "(gibbs default one %s %s)" % (default_num_transitions_per_sample(), in_parallel)
  predictions = collectSamples(ripl,"pid",infer=infer)
  ans = [(False,.471),(True,.529)]
  return reportKnownDiscrete(ans, predictions)

@statisticalTest
@on_inf_prim("gibbs")
def testEnumerativeGibbsCategorical1():
  """Tests mixing when the prior is far from the posterior."""
  ripl = get_ripl()
  ripl.assume('x', '(categorical (simplex 0.1 0.9) (array 0 1))', label="pid")
  ripl.observe('(flip (if (= x 0) 0.9 0.1))', "true")
  
  predictions = collectSamples(ripl, "pid", infer="(gibbs default all 1)")
  ans = [(False, .5), (True, .5)]
  return reportKnownDiscrete(ans, predictions)
  
@gen_on_inf_prim("gibbs")
def testEnumerativeGibbsXOR1():
  yield checkEnumerativeGibbsXOR1, "false"
  yield checkEnumerativeGibbsXOR1, "true"

@statisticalTest
def checkEnumerativeGibbsXOR1(in_parallel):
  """Tests that an XOR chain mixes with enumerative gibbs.
     Note that with RESET=True, this will seem to mix with MH.
     The next test accounts for that."""
  ripl = get_ripl()

  ripl.assume("x","(scope_include 0 0 (bernoulli 0.001))",label="pid")
  ripl.assume("y","(scope_include 0 0 (bernoulli 0.001))")
  ripl.assume("noisy_true","(lambda (pred noise) (flip (if pred 1.0 noise)))")
  ripl.observe("(noisy_true (= (+ x y) 1) .000001)","true")
  infer = "(gibbs 0 0 %s %s)" % (default_num_transitions_per_sample(), in_parallel)
  predictions = collectSamples(ripl,"pid",infer=infer)
  ans = [(True,.5),(False,.5)]
  return reportKnownDiscrete(ans, predictions)

@gen_on_inf_prim("gibbs")
def testEnumerativeGibbsXOR2():
  yield checkEnumerativeGibbsXOR2, "false"
  yield checkEnumerativeGibbsXOR2, "true"

@statisticalTest
def checkEnumerativeGibbsXOR2(in_parallel):
  """Tests that an XOR chain mixes with enumerative gibbs."""
  ripl = get_ripl()

  ripl.assume("x","(scope_include 0 0 (bernoulli 0.0015))",label="pid")
  ripl.assume("y","(scope_include 0 0 (bernoulli 0.0005))")
  ripl.assume("noisy_true","(lambda (pred noise) (flip (if pred 1.0 noise)))")
  ripl.observe("(noisy_true (= (+ x y) 1) .000001)","true")
  infer = "(gibbs 0 0 %s %s)" % (default_num_transitions_per_sample(), in_parallel)
  predictions = collectSamples(ripl,"pid",infer=infer)
  ans = [(True,.75),(False,.25)]
  return reportKnownDiscrete(ans, predictions)

@gen_on_inf_prim("gibbs")
def testEnumerativeGibbsXOR3():
  yield checkEnumerativeGibbsXOR3, "false"
  yield checkEnumerativeGibbsXOR3, "true"

@statisticalTest
def checkEnumerativeGibbsXOR3(in_parallel):
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
  infer = "(gibbs 0 0 %s %s)" % (default_num_transitions_per_sample(), in_parallel)
  predictions = collectSamples(ripl,"pid",infer=infer)
  ans = [(True,.75),(False,.25)]
  return reportKnownDiscrete(ans, predictions)
