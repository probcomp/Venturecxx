import scipy.stats as stats
from nose.tools import eq_, assert_greater, assert_less # Pylint misses metaprogrammed names pylint:disable=no-name-in-module

from venture.test.config import get_ripl, collectSamples, skipWhenRejectionSampling, on_inf_prim
from venture.test.stats import statisticalTest, reportKnownContinuous

@on_inf_prim("none")
def testObserveAVar1a():
  "Observations should propagate through variables."
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.observe("x", 3.0)
  ripl.predict("x", label="pid")
  # TODO assert that ripl.report("pid") is normally distributed here
  ripl.infer("(incorporate)")
  # But the infer should have propagated by here
  eq_(ripl.report("pid"), 3.0)

@on_inf_prim("none")
def testObserveAVar1b():
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.predict("x", label="pid")
  ripl.observe("x", 3.0)
  # TODO assert that ripl.report("pid") is normally distributed here
  ripl.infer("(incorporate)")
  # But the infer should have propagated by here
  eq_(ripl.report("pid"), 3)

@on_inf_prim("none")
def testObserveAMem1a():
  "Observations should propagate through mem."
  ripl = get_ripl()
  ripl.assume("f","(mem (lambda () (normal 0.0 1.0)))")
  ripl.observe("(f)", 3.0)
  ripl.predict("(f)", label="pid")
  # TODO assert that ripl.report("pid") is normally distributed here
  ripl.infer("(incorporate)")
  # But the infer should have propagated by here
  eq_(ripl.report("pid"), 3)

@on_inf_prim("none")
def testObserveAMem1b():
  ripl = get_ripl()
  ripl.assume("f","(mem (lambda () (normal 0.0 1.0)))")
  ripl.predict("(f)", label="pid")
  ripl.observe("(f)", 3.0)
  # TODO assert that ripl.report("pid") is normally distributed here
  ripl.infer("(incorporate)")
  # But the infer should have propagated by here
  eq_(ripl.report("pid"), 3)

@on_inf_prim("none")
def testObserveThenProcessDeterministically1a():
  "Observations should propagate through deterministic SPs."
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.observe("x", 3.0)
  ripl.predict("(* x 5)", label="pid")
  # TODO assert that ripl.report("pid") is normally distributed here
  ripl.infer("(incorporate)")
  # But the infer should have propagated by here
  eq_(ripl.report("pid"), 15)
  
@on_inf_prim("none")
def testObserveThenProcessDeterministically1b():
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.predict("(* x 5)", label="pid")
  ripl.observe("x", 3.0)
  
  # TODO assert that ripl.report("pid") is normally distributed here
  ripl.infer("(incorporate)")
  # But the infer should have propagated by here
  eq_(ripl.report("pid"), 15)

@on_inf_prim("none")
def testObserveThenProcessStochastically1a():
  "Observations should propagate through stochastic SPs without crashing."
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.observe("x", 3.0)
  ripl.predict("(normal x 0.00001)", label="pid")
  # TODO assert that ripl.report("pid") is normally distributed here
  ripl.infer("(incorporate)")
  # But the infer should have propagated by here
  assert_greater(ripl.report("pid"), 2.99)
  assert_less(ripl.report("pid"), 3.01)  
  
@on_inf_prim("none")
def testObserveThenProcessStochastically1b():
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.predict("(normal x 0.00001)", label="pid")
  ripl.observe("x", 3.0)
  
  # TODO assert that ripl.report("pid") is normally distributed here
  ripl.infer("(incorporate)")
  # But the infer should have propagated by here
  assert_greater(ripl.report("pid"), 2.99)
  assert_less(ripl.report("pid"), 3.01)

@skipWhenRejectionSampling("Rejection sampling doesn't work when resimulations of unknown code are observed")
@statisticalTest
def testObserveOutputOfIf1():
  "It is natural to want deterministic conditionals in one's error models.  Some cases Venture can handle gracefully."
  ripl = get_ripl()

  ripl.assume("p","(uniform_continuous 0.0 1.0)",label="pid")
  ripl.assume("x","""
(if (bernoulli p)
    (normal 10.0 1.0)
    (normal 0.0 1.0))
""")
  ripl.observe("x",11.0)

  predictions = collectSamples(ripl,"pid")
  cdf = stats.beta(2,1).cdf # The observation nearly guarantees the first branch is taken
  return reportKnownContinuous(cdf, predictions, "approximately beta(2,1)")
