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

def testConstrainAVar4a():
  raise SkipTest("Issue https://app.asana.com/0/9277419963067/9999884793625")
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")
  ripl.assume("f","(mem (lambda () (scope_include 0 0 (flip))))")
  ripl.predict("(if (f) (* x 5) (* y 5))", label="pid")  
  ripl.observe("(if (f) x y)", 3.0)
  ripl.infer({"kernel":"mh","transitions":20,"scope":0,"block":0})
  eq_(ripl.report("pid"), 15)

def testConstrainAVar4b():
  raise SkipTest("Issue https://app.asana.com/0/9277419963067/9999884793625")
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")
  ripl.assume("f","(mem (lambda () (scope_include 0 0 (flip))))")
  ripl.predict("(if (not (f)) (* x 5) (* y 5))", label="pid")  
  ripl.observe("(if (f) x y)", 3.0)
  ripl.infer({"kernel":"mh","transitions":20,"scope":0,"block":0})
  eq_(ripl.report("pid"), 15)

def testConstrainAVar4c():
  raise SkipTest("Issue https://app.asana.com/0/9277419963067/9999884793625")
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")
  ripl.assume("f","(mem (lambda () (scope_include 0 0 (flip))))")
  ripl.predict("(* x 5)", label="pid")
  ripl.observe("(if (f) x y)", 3.0)
  ripl.infer({"kernel":"mh","transitions":20,"scope":0,"block":0})
  eq_(ripl.report("pid"), 15)

@raises(Exception)  
def testConstrainAVar5a():
"""
    This program is illegal, because when proposing to f, we may end up constraining x,
    which needs to be propagated but the propagation reaches a random choice. This could
    in principal be allowed because there is no exchangeable couping, but for now we have
    decided to allow only deterministic nodes downstream.
"""
  raise SkipTest("Issue https://app.asana.com/0/9277419963067/9999884793625")
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")
  ripl.assume("f","(mem (lambda () (scope_include 0 0 (flip))))")
  ripl.predict("(normal x 0.0001)")
  ripl.observe("(if (f) x y)", 3.0)
  ripl.infer({"kernel":"mh","transitions":20,"scope":0,"block":0})
  eq_(ripl.report("pid"), 15)

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
