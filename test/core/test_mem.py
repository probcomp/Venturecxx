from venture.test.stats import statisticalTest, reportKnownDiscrete
from venture.test.config import get_ripl, collectSamples, on_inf_prim, defaultInfer
from nose.tools import eq_

@on_inf_prim("none")
def testMemSmoke1():
  "Mem should be a noop on deterministic procedures (only memoizing)."
  eq_(get_ripl().predict("((mem (lambda (x) 3)) 1)"), 3.0)

def testMemBasic1():
  "MSPs should always give the same answer when called on the same arguments"
  ripl = get_ripl()
  ripl.assume("f","(mem (lambda () (bernoulli 0.5)))")
  for i in range(10): ripl.predict("(f)",label="p%d" % i)
  for _ in range(5):
    assert reduce(lambda x,y: x == y,[ripl.report("p%d" % i) for i in range(10)])
    ripl.infer(defaultInfer())

def testMemBasic2():
  "MSPs should always give the same answer when called on the same arguments"
  ripl = get_ripl()
  ripl.assume("f","(mem (lambda (x) (bernoulli 0.5)))")
  for i in range(10): ripl.predict("(f 1)",label="p%d" % i)
  for _ in range(5):
    assert reduce(lambda x,y: x == y,[ripl.report("p%d" % i) for i in range(10)])
    ripl.infer(defaultInfer())

def testMemBasic3():
  "MSPs should always give the same answer when called on the same arguments"
  ripl = get_ripl()
  ripl.assume("f","(mem (lambda (x y) (bernoulli 0.5)))")
  for i in range(10): ripl.predict("(f 1 2)",label="p%d" % i)
  for _ in range(5):
    assert reduce(lambda x,y: x == y,[ripl.report("p%d" % i) for i in range(10)])
    ripl.infer(defaultInfer())
            
  
@statisticalTest
@on_inf_prim("any") # Not completely agnostic because uses MH, but
                    # responds to the default inference program
def testMem1():
  "MSPs should deal with their arguments changing under inference."
  ripl = get_ripl()
  ripl.assume("f","(mem (lambda (x) (bernoulli 0.5)))")
  ripl.predict("(f (bernoulli 0.5))")
  ripl.predict("(f (bernoulli 0.5))",label="pid")
  ripl.infer(20) # Run even in crash testing mode
  predictions = collectSamples(ripl, "pid")
  return reportKnownDiscrete([[True, 0.5], [False, 0.5]], predictions)

@statisticalTest
def testMem2():
  "Ensures that all (f 1) and (f 2) are the same"
  ripl = get_ripl()
  ripl.assume("f","(mem (lambda (arg) (categorical (simplex 0.4 0.6) (array 1 2))))")
  ripl.assume("x","(f 1)")
  ripl.assume("y","(f 1)")
  ripl.assume("w","(f 2)")
  ripl.assume("z","(f 2)")
  ripl.assume("q","(categorical (simplex 0.1 0.9) (array 1 2))")
  ripl.predict('(add x y w z q)',label="pid")

  predictions = collectSamples(ripl,"pid")
  # TODO This test can be strengthened by computing more of the ratios in the answer
  # (also by picking constants to have less severe buckets)
  ans = [(5,  0.4 * 0.4 * 0.1),
         (6,  None), (7,  None), (8,  None), (9,  None),
         (10, 0.6 * 0.6 * 0.9)]
  return reportKnownDiscrete(ans, predictions)

@statisticalTest
def testMem3():
  "Same as testMem3 but with booby traps"
  ripl = get_ripl()
  ripl.assume("f","(mem (lambda (arg) (categorical (simplex 0.4 0.6) (array 1 2))))")
  ripl.assume("g","((lambda () (mem (lambda (y) (f (add y 1))))))")
  ripl.assume("x","(f ((if (bernoulli 0.5) (lambda () 1) (lambda () 1))))")
  ripl.assume("y","(g ((lambda () 0)))")
  ripl.assume("w","((lambda () (f 2)))")
  ripl.assume("z","(g 1)")
  ripl.assume("q","(categorical (simplex 0.1 0.9) (array 1 2))")
  ripl.predict('(add x y w z q)',label="pid")

  predictions = collectSamples(ripl,"pid")
  # TODO This test can be strengthened by computing more of the ratios in the answer
  # (also by picking constants to have less severe buckets)
  ans = [(5,  0.4 * 0.4 * 0.1),
         (6,  None), (7,  None), (8,  None), (9,  None),
         (10, 0.6 * 0.6 * 0.9)]
  return reportKnownDiscrete(ans, predictions)

@on_inf_prim("mh")
def testMem4():
  "Like TestMem1, makes sure that MSPs handle changes to their arguments without crashing"
  ripl = get_ripl()
  ripl.assume("pick_a_stick","""
(lambda (sticks k)
  (if (bernoulli (sticks k))
      k
      (pick_a_stick sticks (add k 1))))
""")
  ripl.assume("d","(uniform_continuous 0.4 0.41)")
  ripl.assume("f","(mem (lambda (k) (beta 1.0 (mul k d))))")
  ripl.assume("g","(lambda () (pick_a_stick f 1))")
  ripl.predict("(g)")
  ripl.infer(40)

############ CXX mem tests

def testMemoizingOnAList1():
  """MSP.requestPSP.simulate() needs to quote the values to pass this.
     In CXX, VentureList needs to override several VentureValue methods as well"""
  ripl = get_ripl()
  ripl.assume("f","(mem (lambda (x) (if (flip) 1 1)))")
  ripl.predict("(f (list 0))",label="pid")
  predictions = collectSamples(ripl,"pid",3)
  assert predictions == [1, 1, 1]

def testMemoizingOnASymbol1():
  """MSP.requestPSP.simulate() needs to quote the values to pass this.
     In CXX, VentureSymbol needs to override several VentureValue methods as well"""
  ripl = get_ripl()
  ripl.assume("f","(mem (lambda (x) (if (flip) 1 1)))")
  ripl.predict("(f (quote sym))",label="pid")
  predictions = collectSamples(ripl,"pid",3)
  assert predictions == [1, 1, 1]

# TODO slow to run, and not worth it 
def testMemHashCollisions1():
  """For large A and B, makes sure that MSPs don't allow hash collisions for requests based on
   different arguments."""
  from nose import SkipTest
  raise SkipTest("Skipping testMemHashCollisions1.  Issue https://app.asana.com/0/9277419963067/9801332616438")
  ripl = get_ripl()
  ripl.assume("f","(mem (lambda (a b) (normal 0.0 1.0)))")
  for a in range(1000):
    for b in range(1000):
      ripl.observe("(f %d %d)" % (a,b),"0.5")
