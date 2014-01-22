from venture.test.stats import *
from testconfig import config

def testInferWithNoEntropy():
  "Makes sure that infer doesn't crash when there are no random choices in the trace"
  ripl = config["get_ripl"]()
  ripl.infer(1)
  ripl.predict("(if true 1 2)")
  ripl.infer(1)
  
def testOuterMix1():
  "Makes sure that the mix-mh weights are correct"
  N = config["num_samples"]
  ripl = config["get_ripl"]()
  ripl.predict("(if (bernoulli 0.5) (if (bernoulli 0.5) 2 3) 1)")

  predictions = collectSamples(ripl,1,N)
  ans = [(1,.5), (2,.25), (3,.25)]
  return reportKnownDiscrete("TestOuterMix1", ans, predictions)

def testObserveAPredict1():
  """Tests that constrain propagates the change along
     identity edges. This will fail in all current Ventures."""
  N = config["num_samples"]
  ripl = config["get_ripl"]()
  ripl.assume("f","(mem (lambda () (flip)))")
  ripl.assume("op1","(if (flip) flip (lambda () (f)))")
  ripl.assume("op2","(if (op1) op1 (lambda () (op1)))")
  ripl.assume("op3","(if (op2) op2 (lambda () (op2)))")
  ripl.assume("op4","(if (op3) op2 op1)")
  ripl.predict("(op4)")
  ripl.observe("(op4)",True)
  predictions = collectSamples(ripl,6,N,kernel="mh")
  ans = [(True,0.75), (False,0.25)]
  return reportKnownDiscrete("TestObserveAPredict1", ans, predictions)

def testObserveAPredict2():
  """This test will fail at first, since we previously considered a program like this to be illegal
     and thus did not handle it correctly (we let the predict go stale). So we do not continually
     bewilder our users, I suggest that we handle this case WHEN WE CAN, which means we propagate
     from a constrain as long as we don't hit an absorbing node or a DRG node with a kernel."""
  N = config["num_samples"]
  ripl = config["get_ripl"]()
  ripl.assume("f","(if (flip) (lambda () (normal 0.0 1.0)) (mem (lambda () (normal 0.0 1.0))))")
  ripl.observe("(f)","1.0")
  ripl.predict("(* (f) 100)")
  predictions = collectSamples(ripl,3,N)
  return reportKnownMean("TestObserveAPredict2", 50, predictions)
