from venture.test.stats import *
from nose.tools import *
from nose import SkipTest

def testConstrainAVar1a():
  raise SkipTest("Issue https://app.asana.com/0/9277419963067/9999884793625")
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")  
  ripl.observe("(if (scope_include 0 0 (flip)) x y)", 3.0)
  ripl.predict("x", label="pid")
  ripl.infer({"kernel":"mh","transitions":20,"scope":0,"block":0})
  eq_(ripl.report("pid"), 3)

def testConstrainAVar1b():
  raise SkipTest("Issue https://app.asana.com/0/9277419963067/9999884793625")
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")
  ripl.predict("x", label="pid")  
  ripl.observe("(if (scope_include 0 0 (flip)) x y)", 3.0)
  ripl.infer({"kernel":"mh","transitions":20,"scope":0,"block":0})
  eq_(ripl.report("pid"), 3)
  
def testConstrainAVar2a():
  raise SkipTest("Issue https://app.asana.com/0/9277419963067/9999884793625")
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")
  ripl.assume("f","(mem (lambda () (scope_include 0 0 (flip))))")
  ripl.predict("(if (f) x y)", label="pid")  
  ripl.observe("(if (f) x y)", 3.0)
  ripl.infer({"kernel":"mh","transitions":20,"scope":0,"block":0})
  eq_(ripl.report("pid"), 3)

def testConstrainAVar2b():
  raise SkipTest("Issue https://app.asana.com/0/9277419963067/9999884793625")
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")
  ripl.assume("f","(mem (lambda () (scope_include 0 0 (flip))))")
  ripl.predict("(if (not (f)) x y)", label="pid")  
  ripl.observe("(if (f) x y)", 3.0)
  ripl.infer({"kernel":"mh","transitions":20,"scope":0,"block":0})
  eq_(ripl.report("pid"), 3)

def testConstrainAVar3a():
  raise SkipTest("Issue https://app.asana.com/0/9277419963067/9999884793625")
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")
  ripl.assume("f","(mem (lambda () (flip)))")
  ripl.predict("x", label="pid")  
  ripl.observe("(if (f) x y)", 3.0)
  ripl.observe("(f)","true")
  ripl.infer({"kernel":"mh","transitions":20})
  eq_(ripl.report("pid"), 3)

def testConstrainAVar3b():
  raise SkipTest("Issue https://app.asana.com/0/9277419963067/9999884793625")
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")
  ripl.assume("f","(mem (lambda () (flip)))")
  ripl.observe("(if (f) x y)", 3.0)
  ripl.predict("x", label="pid")      
  ripl.observe("(f)","true")
  ripl.infer({"kernel":"mh","transitions":20})
  eq_(ripl.report("pid"), 3)


@raises(Exception)    
def testConstrainAVar4a():
  """Downstream processing of any kind is currently illegal"""
  raise SkipTest("Issue https://app.asana.com/0/9277419963067/9999884793625")
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")
  ripl.assume("f","(mem (lambda () (scope_include 0 0 (flip))))")
  ripl.predict("(if (f) (* x 5) (* y 5))", label="pid")  
  ripl.observe("(if (f) x y)", 3.0)
  ripl.infer({"kernel":"mh","transitions":20,"scope":0,"block":0})

@raises(Exception)    
def testConstrainAVar4b():
  raise SkipTest("Issue https://app.asana.com/0/9277419963067/9999884793625")
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")
  ripl.assume("f","(mem (lambda () (scope_include 0 0 (flip))))")
  ripl.predict("(if (not (f)) (* x 5) (* y 5))", label="pid")  
  ripl.observe("(if (f) x y)", 3.0)
  ripl.infer({"kernel":"mh","transitions":20,"scope":0,"block":0})

@raises(Exception)    
def testConstrainAVar4c():
  raise SkipTest("Issue https://app.asana.com/0/9277419963067/9999884793625")
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")
  ripl.assume("f","(mem (lambda () (scope_include 0 0 (flip))))")
  ripl.predict("(* x 5)", label="pid")
  ripl.observe("(if (f) x y)", 3.0)
  ripl.infer({"kernel":"mh","transitions":20,"scope":0,"block":0})

@raises(Exception)  
def testConstrainAVar5a():
"""
    This program is illegal, because when proposing to f, we may end up constraining x,
    which needs to be propagated but the propagation reaches a random choice. This could
    in principal be allowed because there is no exchangeable couping, but for now we have
    decided to forbid all non-identity downstream edges.
"""
  raise SkipTest("Issue https://app.asana.com/0/9277419963067/9999884793625")
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")
  ripl.assume("f","(mem (lambda () (scope_include 0 0 (flip))))")
  ripl.predict("(normal x 0.0001)")
  ripl.observe("(if (f) x y)", 3.0)
  ripl.infer({"kernel":"mh","transitions":20,"scope":0,"block":0})

@raises(Exception)  
def testConstrainAVar5b():
"""
    This program is illegal, because when proposing to f, we may end up constraining x,
    and x has a child in A (it is in the (new)brush itself).
"""
  raise SkipTest("Issue https://app.asana.com/0/9277419963067/9999884793625")
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")
  ripl.assume("f","(mem (lambda () (scope_include 0 0 (flip))))")
  ripl.predict("(if (f) (normal x 0.0001) (normal y 0.0001))")
  ripl.observe("(if (f) x y)", 3.0)
  ripl.infer({"kernel":"mh","transitions":20,"scope":0,"block":0})

@statisticalTest
def testConstrainWithAPredict1():
  """Tests that constrain propagates the change along identity edges,
     even unto if branches and mems.  Daniel says "This will fail in
     all current Ventures", but what the correct behavior would even
     be is mysterious to Alexey."""
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
def testConstrainWithAPredict2():
  """This test will fail at first, since we previously considered a program like this to be illegal
     and thus did not handle it correctly (we let the predict go stale). So we do not continually
     bewilder our users, I suggest that we handle this case WHEN WE CAN, which means we propagate
     from a constrain as long as we don't hit an absorbing node or a DRG node with a kernel."""
  ripl = get_ripl()
  ripl.assume("f","(if (flip) (lambda () (normal 0.0 1.0)) (mem (lambda () (normal 0.0 1.0))))")
  ripl.observe("(f)","1.0")
  ripl.predict("(* (f) 100)")
  predictions = collectSamples(ripl,3)
  return reportKnownMean("TestObserveAPredict2", 50, predictions)
  
