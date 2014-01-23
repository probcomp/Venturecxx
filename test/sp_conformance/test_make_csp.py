from venture.test.stats import *
from testconfig import config
from nose.tools import assert_equals

def testMakeCSP1():
  ripl = config["get_ripl"]()
  ripl.assume("f", "(lambda (x) (* x x))")
  ripl.predict("(f 1)")
  assert_equals(ripl.report(2),1.0)

def testMakeCSP2():  
  ripl = config["get_ripl"]()
  ripl.assume("g", "(lambda (x y) (* x y))")
  ripl.predict("(g 2 3)")
  assert_equals(ripl.report(2),6.0)

def testMakeCSP3():  
  ripl = config["get_ripl"]()
  ripl.assume("h", "(lambda () 5)")
  ripl.predict("(h)")
  assert_equals(ripl.report(2),5.0)

def testMakeCSP4():  
  ripl = config["get_ripl"]()
  ripl.assume("f", "(lambda (x y z) (lambda (u v w) (lambda () (+ (* x u) (* y v) (* z w)))))")
  ripl.assume("g", "(f 10 20 30)")
  ripl.assume("h","(g 3 5 7)")
  ripl.predict("(h)",label="pid")
  assert_equals(ripl.report("pid"),340)
