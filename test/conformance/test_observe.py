from venture.test.config import get_ripl
from nose.tools import eq_, assert_greater, assert_less # Pylint misses metaprogrammed names pylint:disable=no-name-in-module

def testObserveAVar1a():
  "Observations should propagate through variables."
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.observe("x", 3.0)
  ripl.predict("x", label="pid")
  # TODO assert that ripl.report("pid") is normally distributed here
  ripl.infer(1)
  # But the infer should have propagated by here
  eq_(ripl.report("pid"), 3.0)

def testObserveAVar1b():
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.predict("x", label="pid")
  ripl.observe("x", 3.0)
  # TODO assert that ripl.report("pid") is normally distributed here
  ripl.infer(1)
  # But the infer should have propagated by here
  eq_(ripl.report("pid"), 3)

def testObserveAMem1a():
  "Observations should propagate through mem."
  ripl = get_ripl()
  ripl.assume("f","(mem (lambda () (normal 0.0 1.0)))")
  ripl.observe("(f)", 3.0)
  ripl.predict("(f)", label="pid")
  # TODO assert that ripl.report("pid") is normally distributed here
  ripl.infer(1)
  # But the infer should have propagated by here
  eq_(ripl.report("pid"), 3)

def testObserveAMem1b():
  ripl = get_ripl()
  ripl.assume("f","(mem (lambda () (normal 0.0 1.0)))")
  ripl.predict("(f)", label="pid")
  ripl.observe("(f)", 3.0)
  # TODO assert that ripl.report("pid") is normally distributed here
  ripl.infer(1)
  # But the infer should have propagated by here
  eq_(ripl.report("pid"), 3)

def testObserveThenProcessDeterministically1a():
  "Observations should propagate through deterministic SPs."
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.observe("x", 3.0)
  ripl.predict("(* x 5)", label="pid")
  # TODO assert that ripl.report("pid") is normally distributed here
  ripl.infer(1)
  # But the infer should have propagated by here
  eq_(ripl.report("pid"), 15)
  
def testObserveThenProcessDeterministically1b():
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.predict("(* x 5)", label="pid")
  ripl.observe("x", 3.0)
  
  # TODO assert that ripl.report("pid") is normally distributed here
  ripl.infer(1)
  # But the infer should have propagated by here
  eq_(ripl.report("pid"), 15)

def testObserveThenProcessStochastically1a():
  "Observations should propagate through stochastic SPs without crashing."
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.observe("x", 3.0)
  ripl.predict("(normal x 0.00001)", label="pid")
  # TODO assert that ripl.report("pid") is normally distributed here
  ripl.infer(1)
  # But the infer should have propagated by here
  assert_greater(ripl.report("pid"), 2.99)
  assert_less(ripl.report("pid"), 3.01)  
  
def testObserveThenProcessStochastically1b():
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.predict("(normal x 0.00001)", label="pid")
  ripl.observe("x", 3.0)
  
  # TODO assert that ripl.report("pid") is normally distributed here
  ripl.infer(1)
  # But the infer should have propagated by here
  assert_greater(ripl.report("pid"), 2.99)
  assert_less(ripl.report("pid"), 3.01)  
      
