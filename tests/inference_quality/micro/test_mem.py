from venture.shortcuts import *
from stat_helpers import *
from test_globals import N, globalKernel

def RIPL(): return make_lite_church_prime_ripl()

def testMem1():
  "This test used to cause CXX to crash"
  ripl = RIPL()
  ripl.assume("f","(mem (lambda (x) (bernoulli 0.5)))")
  ripl.predict("(f (bernoulli 0.5))")
  ripl.predict("(f (bernoulli 0.5))")
  ripl.infer(N)
  return reportPassage("TestMem1")

def testMem2():
  "Ensures that all (f 1) and (f 2) are the same"
  ripl = RIPL()
  ripl.assume("f","(mem (lambda (arg) (categorical (simplex 0.4 0.6) (array 1 2))))")
  ripl.assume("x","(f 1)")
  ripl.assume("y","(f 1)")
  ripl.assume("w","(f 2)")
  ripl.assume("z","(f 2)")
  ripl.assume("q","(categorical (simplex 0.1 0.9) (array 1 2))))")
  ripl.predict('(plus x y w z q)');

  predictions = collectSamples(ripl,7,N)
  # TODO This test can be strengthened by computing more of the ratios in the answer
  # (also by picking constants to have less severe buckets)
  ans = [(5,  0.4 * 0.4 * 0.1),
         (6,  None), (7,  None), (8,  None), (9,  None),
         (10, 0.6 * 0.6 * 0.9)]
  return reportKnownDiscrete("TestMem2", ans, predictions)

def testMem3(N):
  "Same as testMem3 but with booby traps"
  ripl = RIPL()
  ripl.assume("f","(mem (lambda (arg) (categorical (simplex 0.4 0.6) (array 1 2))))")
  ripl.assume("g","((lambda () (mem (lambda (y) (f (plus y 1))))))")
  ripl.assume("x","(f ((if (bernoulli 0.5) (lambda () 1) (lambda () 1))))")
  ripl.assume("y","(g ((lambda () 0)))")
  ripl.assume("w","((lambda () (f 2)))")
  ripl.assume("z","(g 1)")
  ripl.assume("q","(categorical (simplex 0.1 0.9) (array 1 2))")
  ripl.predict('(plus x y w z q)');

  predictions = collectSamples(ripl,8,N)
  # TODO This test can be strengthened by computing more of the ratios in the answer
  # (also by picking constants to have less severe buckets)
  ans = [(5,  0.4 * 0.4 * 0.1),
         (6,  None), (7,  None), (8,  None), (9,  None),
         (10, 0.6 * 0.6 * 0.9)]
  return reportKnownDiscrete("TestMem3", ans, predictions)

