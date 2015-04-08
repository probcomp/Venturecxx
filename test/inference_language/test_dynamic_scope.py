from nose.tools import assert_equal

from venture.test.config import get_ripl, on_inf_prim

@on_inf_prim("none")
def testDynamicScope1():
  ripl = get_ripl()
  ripl.assume("x", "(normal 0.0 1.0)")
  ripl.predict("(tag 0 0 (normal x 1))")
  assert_equal(ripl.sivm.core_sivm.engine.getDistinguishedTrace().numNodesInBlock(0,0),1)

@on_inf_prim("none")
def testDynamicScope2():
  ripl = get_ripl()
  ripl.assume("x", "(normal 0.0 1.0)")
  ripl.predict("(tag 0 0 (normal (normal x 1) 1))")
  assert_equal(ripl.sivm.core_sivm.engine.getDistinguishedTrace().numNodesInBlock(0,0),2)

@on_inf_prim("none")
def testDynamicScope3():
  ripl = get_ripl()
  ripl.assume("x", "(normal 0.0 1.0)")
  ripl.assume("f", "(lambda () (normal x 1.0))")  
  ripl.predict("(tag 0 0 (normal (normal (f) 1) 1))")
  assert_equal(ripl.sivm.core_sivm.engine.getDistinguishedTrace().numNodesInBlock(0,0),3)

@on_inf_prim("none")
def testDynamicScope4():
  ripl = get_ripl()
  ripl.assume("x", "(normal 0.0 1.0)")
  ripl.assume("f", "(mem (lambda () (normal x 1.0)))")  
  ripl.predict("(tag 0 0 (normal (+ (f) (normal (f) 1) (normal 0 1)) 1))")
  assert_equal(ripl.sivm.core_sivm.engine.getDistinguishedTrace().numNodesInBlock(0,0),4)

@on_inf_prim("none")
def testDynamicScope5():
  ripl = get_ripl()
  ripl.assume("x", "(tag 0 0 (normal 0.0 1.0))")
  ripl.assume("f", "(mem (lambda () (normal x 1.0)))")  
  ripl.predict("(tag 0 0 (normal (+ (f) (normal (f) 1) (normal 0 1)) 1))")
  assert_equal(ripl.sivm.core_sivm.engine.getDistinguishedTrace().numNodesInBlock(0,0),5)
    
@on_inf_prim("none")
def testDynamicScope6():
  ripl = get_ripl()
  ripl.assume("x", "(normal 0.0 1.0)")
  ripl.assume("f", "(mem (lambda () (tag 0 1 (normal x 1.0))))")  
  ripl.predict("(tag 0 0 (normal (+ (f) (normal (f) 1) (normal 0 1)) 1))")
  assert_equal(ripl.sivm.core_sivm.engine.getDistinguishedTrace().numNodesInBlock(0,0),3)

@on_inf_prim("none")
def testDynamicScope6a():
  ripl = get_ripl()
  ripl.assume("x", "(normal 0.0 1.0)")
  ripl.assume("f", "(mem (lambda () (tag 0 0 (normal x 1.0))))")  
  ripl.predict("(tag 0 0 (normal (+ (f) (normal (f) 1) (normal 0 1)) 1))")
  assert_equal(ripl.sivm.core_sivm.engine.getDistinguishedTrace().numNodesInBlock(0,0),4)

@on_inf_prim("none")
def testDynamicScope7():
  ripl = get_ripl()
  ripl.assume("x", "(normal 0.0 1.0)")
  ripl.assume("f", "(mem (lambda () (tag 1 0 (normal x 1.0))))")  
  ripl.predict("(tag 0 0 (normal (+ (f) (normal (f) 1) (normal 0 1)) 1))")
  assert_equal(ripl.sivm.core_sivm.engine.getDistinguishedTrace().numNodesInBlock(0,0),4)

@on_inf_prim("none")
def testDynamicScope8():
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("f","(mem (lambda () (tag 1 0 (normal x 1.0))))")
  ripl.assume("g","(lambda (z) (normal (+ (f) (tag 0 0 (normal (f) 1)) (normal z 1)) 1))")
  ripl.predict("(tag 0 0 (+ (g (bernoulli)) (g (bernoulli))))")
  assert_equal(ripl.sivm.core_sivm.engine.getDistinguishedTrace().numNodesInBlock(0,0),9)

@on_inf_prim("none")
def testScopeExclude1():
  ripl = get_ripl()
  ripl.assume("f", "(mem (lambda (x) (scope_exclude 0 (bernoulli))))")
  ripl.predict("(tag 0 0 (+ (f 0) (f 1) (f 2) (f 3)))")
  assert_equal(ripl.sivm.core_sivm.engine.getDistinguishedTrace().numNodesInBlock(0, 0), 0)

@on_inf_prim("none")
def testScopeExcludeBaseline():
  ripl = get_ripl()
  ripl.assume("f", "(mem (lambda (x) (bernoulli)))")
  ripl.predict("(tag 0 0 (+ (f 0) (f 1) (f 2) (f 3)))")
  assert_equal(ripl.sivm.core_sivm.engine.getDistinguishedTrace().numNodesInBlock(0, 0), 4)

