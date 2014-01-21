from venture.shortcuts import *
from stat_helpers import *
from test_globals import N, globalKernel

def RIPL(): return make_lite_church_prime_ripl()

def testMakeCSP1():
  ripl = RIPL()
  ripl.assume("f", "(lambda (x) (* x x))")
  ripl.predict("(f 1)")
  assert(ripl.report(2) == 1.0)

def testMakeCSP2():  
  ripl = RIPL()
  ripl.assume("g", "(lambda (x y) (* x y))")
  ripl.predict("(g 2 3)")
  assert(ripl.report(2) == 6.0)

def testMakeCSP3():  
  ripl = RIPL()
  ripl.assume("h", "(lambda () 5)")
  ripl.predict("(h)")
  assert(ripl.report(2) == 5.0)
