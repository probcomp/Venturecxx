from testconfig import config
from nose import SkipTest
from venture.test.config import get_ripl
from nose.tools import assert_equal

def testDynamicScope1():
  ripl = get_ripl()
  if config["get_ripl"] != "lite": raise SkipTest("This test is not supported by CXX yet")
  
  ripl.assume("x", "(normal 0.0 1.0)")
  ripl.predict("(scope_include 0 0 (normal x 1))")
  assert_equal(len(ripl.sivm.core_sivm.engine.trace.getNodesInBlock(0,0)),1)

def testDynamicScope2():
  ripl = get_ripl()
  if config["get_ripl"] != "lite": raise SkipTest("This test is not supported by CXX yet")
  
  ripl.assume("x", "(normal 0.0 1.0)")
  ripl.predict("(scope_include 0 0 (normal (normal x 1) 1))")
  assert_equal(len(ripl.sivm.core_sivm.engine.trace.getNodesInBlock(0,0)),2)

def testDynamicScope3():
  ripl = get_ripl()
  if config["get_ripl"] != "lite": raise SkipTest("This test is not supported by CXX yet")
  
  ripl.assume("x", "(normal 0.0 1.0)")
  ripl.assume("f", "(lambda () (normal x 1.0))")  
  ripl.predict("(scope_include 0 0 (normal (normal (f) 1) 1))")
  assert_equal(len(ripl.sivm.core_sivm.engine.trace.getNodesInBlock(0,0)),3)

def testDynamicScope4():
  ripl = get_ripl()
  if config["get_ripl"] != "lite": raise SkipTest("This test is not supported by CXX yet")
  
  ripl.assume("x", "(normal 0.0 1.0)")
  ripl.assume("f", "(mem (lambda () (normal x 1.0)))")  
  ripl.predict("(scope_include 0 0 (normal (+ (f) (normal (f) 1) (normal 0 1)) 1))")
  assert_equal(len(ripl.sivm.core_sivm.engine.trace.getNodesInBlock(0,0)),4)

def testDynamicScope5():
  ripl = get_ripl()
  if config["get_ripl"] != "lite": raise SkipTest("This test is not supported by CXX yet")
  
  ripl.assume("x", "(scope_include 0 0 (normal 0.0 1.0))")
  ripl.assume("f", "(mem (lambda () (normal x 1.0)))")  
  ripl.predict("(scope_include 0 0 (normal (+ (f) (normal (f) 1) (normal 0 1)) 1))")
  assert_equal(len(ripl.sivm.core_sivm.engine.trace.getNodesInBlock(0,0)),5)
    
def testDynamicScope6():
  ripl = get_ripl()
  if config["get_ripl"] != "lite": raise SkipTest("This test is not supported by CXX yet")
  
  ripl.assume("x", "(normal 0.0 1.0)")
  ripl.assume("f", "(mem (lambda () (scope_include 0 1 (normal x 1.0))))")  
  ripl.predict("(scope_include 0 0 (normal (+ (f) (normal (f) 1) (normal 0 1)) 1))")
  assert_equal(len(ripl.sivm.core_sivm.engine.trace.getNodesInBlock(0,0)),3)

def testDynamicScope6a():
  ripl = get_ripl()
  if config["get_ripl"] != "lite": raise SkipTest("This test is not supported by CXX yet")
  
  ripl.assume("x", "(normal 0.0 1.0)")
  ripl.assume("f", "(mem (lambda () (scope_include 0 0 (normal x 1.0))))")  
  ripl.predict("(scope_include 0 0 (normal (+ (f) (normal (f) 1) (normal 0 1)) 1))")
  assert_equal(len(ripl.sivm.core_sivm.engine.trace.getNodesInBlock(0,0)),4)

def testDynamicScope7():
  ripl = get_ripl()
  if config["get_ripl"] != "lite": raise SkipTest("This test is not supported by CXX yet")
  
  ripl.assume("x", "(normal 0.0 1.0)")
  ripl.assume("f", "(mem (lambda () (scope_include 1 0 (normal x 1.0))))")  
  ripl.predict("(scope_include 0 0 (normal (+ (f) (normal (f) 1) (normal 0 1)) 1))")
  assert_equal(len(ripl.sivm.core_sivm.engine.trace.getNodesInBlock(0,0)),4)

def testDynamicScope8():
  ripl = get_ripl()
  if config["get_ripl"] != "lite": raise SkipTest("This test is not supported by CXX yet")
  
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("f","(mem (lambda () (scope_include 1 0 (normal x 1.0))))")
  ripl.assume("g","(lambda (z) (normal (+ (f) (scope_include 0 0 (normal (f) 1)) (normal z 1)) 1))")
  ripl.predict("(scope_include 0 0 (+ (g (flip)) (g (flip))))")
  assert_equal(len(ripl.sivm.core_sivm.engine.trace.getNodesInBlock(0,0)),9)
          
      
