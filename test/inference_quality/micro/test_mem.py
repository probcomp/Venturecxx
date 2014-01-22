from venture.test.stats import *
from testconfig import config

def testMem1():
  "This test used to cause CXX to crash"
  ripl = config["get_ripl"]()
  ripl.assume("f","(mem (lambda (x) (bernoulli 0.5)))")
  ripl.predict("(f (bernoulli 0.5))")
  ripl.predict("(f (bernoulli 0.5))")
  ripl.infer(20)
  return reportPassage("TestMem1")

def testMem2():
  "Ensures that all (f 1) and (f 2) are the same"
  ripl = config["get_ripl"]()
  ripl.assume("f","(mem (lambda (arg) (categorical (simplex 0.4 0.6) (array 1 2))))")
  ripl.assume("x","(f 1)")
  ripl.assume("y","(f 1)")
  ripl.assume("w","(f 2)")
  ripl.assume("z","(f 2)")
  ripl.assume("q","(categorical (simplex 0.1 0.9) (array 1 2))")
  ripl.predict('(plus x y w z q)',label="pid");

  predictions = collectSamples(ripl,"pid")
  # TODO This test can be strengthened by computing more of the ratios in the answer
  # (also by picking constants to have less severe buckets)
  ans = [(5,  0.4 * 0.4 * 0.1),
         (6,  None), (7,  None), (8,  None), (9,  None),
         (10, 0.6 * 0.6 * 0.9)]
  return reportKnownDiscrete("TestMem2", ans, predictions)

def testMem3():
  "Same as testMem3 but with booby traps"
  ripl = config["get_ripl"]()
  ripl.assume("f","(mem (lambda (arg) (categorical (simplex 0.4 0.6) (array 1 2))))")
  ripl.assume("g","((lambda () (mem (lambda (y) (f (plus y 1))))))")
  ripl.assume("x","(f ((if (bernoulli 0.5) (lambda () 1) (lambda () 1))))")
  ripl.assume("y","(g ((lambda () 0)))")
  ripl.assume("w","((lambda () (f 2)))")
  ripl.assume("z","(g 1)")
  ripl.assume("q","(categorical (simplex 0.1 0.9) (array 1 2))")
  ripl.predict('(plus x y w z q)');

  predictions = collectSamples(ripl,8)
  # TODO This test can be strengthened by computing more of the ratios in the answer
  # (also by picking constants to have less severe buckets)
  ans = [(5,  0.4 * 0.4 * 0.1),
         (6,  None), (7,  None), (8,  None), (9,  None),
         (10, 0.6 * 0.6 * 0.9)]
  return reportKnownDiscrete("TestMem3", ans, predictions)

def testMem4():
  "Like TestMem1, makes sure that MSPs handle changes to their arguments without crashing"
  ripl = config["get_ripl"]()
  ripl.assume("pick_a_stick","""
(lambda (sticks k)
  (if (bernoulli (sticks k))
      k
      (pick_a_stick sticks (plus k 1))))
""")
  ripl.assume("d","(uniform_continuous 0.4 0.41)")
  ripl.assume("f","(mem (lambda (k) (beta 1.0 (times k d))))")
  ripl.assume("g","(lambda () (pick_a_stick f 1))")
  ripl.predict("(g)")
  ripl.infer(40)
  return reportPassage("TestMem4")

############ CXX mem tests

def testMemoizingOnAList1():
  """MSP.requestPSP.simulate() needs to quote the values to pass this.
     In CXX, VentureList needs to override several VentureValue methods as well"""
  ripl = config["get_ripl"]()
  ripl.assume("f","(mem (lambda (x) (flip)))")
  ripl.predict("(f (list 0))",label="pid")
  predictions = collectSamples(ripl,"pid",1)
  assert predictions == [1]
  return reportPassage("TestMemoizingOnAList")

def testMemoizingOnASymbol1():
  """MSP.requestPSP.simulate() needs to quote the values to pass this.
     In CXX, VentureSymbol needs to override several VentureValue methods as well"""
  ripl = config["get_ripl"]()
  ripl.assume("f","(mem (lambda (x) (if (flip) 1 1)))")
  ripl.predict("(f (quote sym))",label="pid")
  predictions = collectSamples(ripl,"pid",1)
  assert predictions == [1]
  return reportPassage("TestMemoizingOnASymbol")

# TODO slow to run, and not worth it 
def testMemHashCollisions1():
  """For large A and B, makes sure that MSPs don't allow hash collisions for requests based on
   different arguments."""
  from nose import SkipTest
  raise SkipTest("Skipping testMemHashCollisions1")
  ripl = config["get_ripl"]()
  ripl.assume("f","(mem (lambda (a b) (normal 0.0 1.0)))")
  for a in range(1000):
    for b in range(1000):
      ripl.observe("(f %d %d)" % (a,b),"0.5")
  return reportPassage("TestMemHashFunction(%d,%d)" % (A,B))
