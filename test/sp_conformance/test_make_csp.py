from venture.test.stats import *
from testconfig import config

def testMakeCSP1():
  ripl = config["get_ripl"]()
  ripl.assume("f", "(lambda (x) (* x x))")
  ripl.predict("(f 1)")
  assert(ripl.report(2) == 1.0)

def testMakeCSP2():  
  ripl = config["get_ripl"]()
  ripl.assume("g", "(lambda (x y) (* x y))")
  ripl.predict("(g 2 3)")
  assert(ripl.report(2) == 6.0)

def testMakeCSP3():  
  ripl = config["get_ripl"]()
  ripl.assume("h", "(lambda () 5)")
  ripl.predict("(h)")
  assert(ripl.report(2) == 5.0)
