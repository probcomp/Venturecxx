from venture.test.stats import *
from nose.tools import *
from nose import SkipTest

def testObserveAVar1a():
  "Observations should propagate through variables."
  raise SkipTest("Issue https://app.asana.com/0/9277419963067/9999884793625")
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.observe("x", 3.0)
  ripl.predict("x", label="pid")
  # TODO assert that ripl.report("pid") is normally distributed here
  ripl.infer(1)
  # But the infer should have propagated by here
  eq_(ripl.report("pid"), 3)

def testObserveAVar1b():
  raise SkipTest("Issue https://app.asana.com/0/9277419963067/9999884793625")
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
  raise SkipTest("Issue https://app.asana.com/0/9277419963067/9999884793625")
  ripl = get_ripl()
  ripl.assume("f","(mem (lambda () (normal 0.0 1.0)))")
  ripl.observe("(f)", 3.0)
  ripl.predict("(f)", label="pid")
  # TODO assert that ripl.report("pid") is normally distributed here
  ripl.infer(1)
  # But the infer should have propagated by here
  eq_(ripl.report("pid"), 3)

def testObserveAMem1b():
  raise SkipTest("Issue https://app.asana.com/0/9277419963067/9999884793625")
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
  raise SkipTest("Issue https://app.asana.com/0/9277419963067/9999884793625")
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.observe("x", 3.0)
  ripl.predict("(* x 5)", label="pid")
  # TODO assert that ripl.report("pid") is normally distributed here
  ripl.infer(1)
  # But the infer should have propagated by here
  eq_(ripl.report("pid"), 15)
  
def testObserveThenProcessDeterministically1b():
  raise SkipTest("Issue https://app.asana.com/0/9277419963067/9999884793625")
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
  raise SkipTest("Issue https://app.asana.com/0/9277419963067/9999884793625")
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.observe("x", 3.0)
  ripl.predict("(normal x 0.00001)", label="pid")
  # TODO assert that ripl.report("pid") is normally distributed here
  ripl.infer(1)
  # But the infer should have propagated by here
  assert_greater_than(ripl.report("pid"), 2.99)
  assert_less_than(ripl.report("pid"), 3.01)  
  
def testObserveThenProcessStochastically1b():
  raise SkipTest("Issue https://app.asana.com/0/9277419963067/9999884793625")
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.predict("(normal x 0.00001)", label="pid")
  ripl.observe("x", 3.0)
  
  # TODO assert that ripl.report("pid") is normally distributed here
  ripl.infer(1)
  # But the infer should have propagated by here
  assert_greater_than(ripl.report("pid"), 2.99)
  assert_less_than(ripl.report("pid"), 3.01)  
      
@statisticalTest
def testObserveAPredict1():
  """Tests that constrain propagates the change along identity edges,
     even unto if branches and mems.  Daniel says "This will fail in
     all current Ventures", but what the correct behavior would even
     be is mysterious to Alexey."""
  raise SkipTest("What is the testObserveAPredict1 program even supposed to do?  Issue https://app.asana.com/0/9277419963067/9801332616425")
  ripl = get_ripl()
  ripl.assume("f","(mem (lambda () (flip)))")
  ripl.assume("op1","(if (flip) flip (lambda () (f)))")
  ripl.assume("op2","(if (op1) op1 (lambda () (op1)))")
  ripl.assume("op3","(if (op2) op2 (lambda () (op2)))")
  ripl.assume("op4","(if (op3) op2 op1)")
  ripl.predict("(op4)")
  ripl.observe("(op4)",True)
  predictions = collectSamples(ripl,6)
  ans = [(True,0.75), (False,0.25)]
  return reportKnownDiscrete("TestObserveAPredict1", ans, predictions)

@statisticalTest
def testObserveAPredict2():
  """This test will fail at first, since we previously considered a program like this to be illegal
     and thus did not handle it correctly (we let the predict go stale). So we do not continually
     bewilder our users, I suggest that we handle this case WHEN WE CAN, which means we propagate
     from a constrain as long as we don't hit an absorbing node or a DRG node with a kernel."""
  raise SkipTest("This failure appears to be a more elaborate version of testObserveAMem1, so skip it.  Issue https://app.asana.com/0/9277419963067/9801332616425")
  ripl = get_ripl()
  ripl.assume("f","(if (flip) (lambda () (normal 0.0 1.0)) (mem (lambda () (normal 0.0 1.0))))")
  ripl.observe("(f)","1.0")
  ripl.predict("(* (f) 100)")
  predictions = collectSamples(ripl,3)
  return reportKnownMean("TestObserveAPredict2", 50, predictions)
