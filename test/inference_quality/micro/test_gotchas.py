from venture.test.stats import *
from nose.tools import *
from nose import SkipTest
from testconfig import config

def testInferWithNoEntropy():
  "Makes sure that infer doesn't crash when there are no random choices in the trace"
  ripl = config["get_ripl"]()
  ripl.infer(1)
  ripl.predict("(if true 1 2)")
  ripl.infer(1)
  
@statisticalTest
def testOuterMix1():
  "Makes sure that the mix-mh weights are correct"
  ripl = config["get_ripl"]()
  ripl.predict("(if (bernoulli 0.5) (if (bernoulli 0.5) 2 3) 1)")

  predictions = collectSamples(ripl,1)
  ans = [(1,.5), (2,.25), (3,.25)]
  return reportKnownDiscrete("TestOuterMix1", ans, predictions)

def testObserveAMem1():
  "So, how should observe interact with mem?"
  raise SkipTest("How should observe interact with mem?  Issue https://app.asana.com/0/9277419963067/9801332616425")
  ripl = config["get_ripl"]()
  ripl.assume("f","(mem (lambda () (normal 0.0 1.0)))")
  ripl.observe("(f)", 3.0)
  ripl.predict("(f)", label="pid")
  ripl.infer(5) # Should be enough to solve itself, if that worked.
  eq_(ripl.report("pid"), 3)

@statisticalTest
def testObserveAPredict1():
  """Tests that constrain propagates the change along identity edges,
     even unto if branches and mems.  Daniel says "This will fail in
     all current Ventures", but what the correct behavior would even
     be is mysterious to Alexey."""
  raise SkipTest("What is the testObserveAPredict1 program even supposed to do?  Issue https://app.asana.com/0/9277419963067/9801332616425")
  ripl = config["get_ripl"]()
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
  ripl = config["get_ripl"]()
  ripl.assume("f","(if (flip) (lambda () (normal 0.0 1.0)) (mem (lambda () (normal 0.0 1.0))))")
  ripl.observe("(f)","1.0")
  ripl.predict("(* (f) 100)")
  predictions = collectSamples(ripl,3)
  return reportKnownMean("TestObserveAPredict2", 50, predictions)
