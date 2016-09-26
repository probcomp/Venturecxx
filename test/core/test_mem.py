# Copyright (c) 2013, 2014, 2015 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

from nose.tools import eq_, assert_raises_regexp

from venture.test.config import collectSamples
from venture.test.config import defaultInfer
from venture.test.config import get_ripl
from venture.test.config import on_inf_prim
from venture.test.config import skipWhenSubSampling
from venture.test.stats import reportKnownDiscrete
from venture.test.stats import statisticalTest

def all_equal(results):
  iresults = iter(results)
  first = next(iresults)
  return all(result == first for result in iresults)

@on_inf_prim("none")
def testMemSmoke1():
  # Mem should be a noop on deterministic procedures (only memoizing).
  eq_(get_ripl().predict("((mem (lambda (x) 3)) 1)"), 3.0)

@skipWhenSubSampling("Subsampling the consequences causes them to become stale")
def testMemBasic1():
  # MSPs should always give the same answer when called on the same arguments
  ripl = get_ripl()
  ripl.assume("f","(mem (lambda () (bernoulli 0.5)))")
  for i in range(10): ripl.predict("(f)",label="p%d" % i)
  for _ in range(5):
    assert all_equal([ripl.report("p%d" % i) for i in range(10)])
    ripl.infer(defaultInfer())

@skipWhenSubSampling("Subsampling the consequences causes them to become stale")
def testMemBasic2():
  # MSPs should always give the same answer when called on the same arguments
  ripl = get_ripl()
  ripl.assume("f","(mem (lambda (x) (bernoulli 0.5)))")
  for i in range(10): ripl.predict("(f 1)",label="p%d" % i)
  for _ in range(5):
    assert all_equal([ripl.report("p%d" % i) for i in range(10)])
    ripl.infer(defaultInfer())

@skipWhenSubSampling("Subsampling the consequences causes them to become stale")
def testMemBasic3():
  # MSPs should always give the same answer when called on the same arguments
  ripl = get_ripl()
  ripl.assume("f","(mem (lambda (x y) (bernoulli 0.5)))")
  for i in range(10): ripl.predict("(f 1 2)",label="p%d" % i)
  for _ in range(5):
    assert all_equal([ripl.report("p%d" % i) for i in range(10)])
    ripl.infer(defaultInfer())
            
  
@statisticalTest
@on_inf_prim("any") # Not completely agnostic because uses MH, but
                    # responds to the default inference program
def testMem1(seed):
  # MSPs should deal with their arguments changing under inference.
  ripl = get_ripl(seed=seed)
  ripl.assume("f","(mem (lambda (x) (bernoulli 0.5)))")
  ripl.predict("(f (bernoulli 0.5))")
  ripl.predict("(f (bernoulli 0.5))",label="pid")
  ripl.infer(20) # Run even in crash testing mode
  predictions = collectSamples(ripl, "pid")
  return reportKnownDiscrete([[True, 0.5], [False, 0.5]], predictions)

@statisticalTest
def testMem2(seed):
  # Ensures that all (f 1) and (f 2) are the same
  ripl = get_ripl(seed=seed)
  ripl.assume("f","(mem (lambda (arg) (categorical (simplex 0.4 0.6) (array 1 2))))")
  ripl.assume("x","(f 1)")
  ripl.assume("y","(f 1)")
  ripl.assume("w","(f 2)")
  ripl.assume("z","(f 2)")
  ripl.assume("q","(categorical (simplex 0.1 0.9) (array 1 2))")
  ripl.predict('(add x y w z q)',label="pid")

  predictions = collectSamples(ripl,"pid")
  ans = [(5,  0.4 * 0.4 * 0.1),
         (6,  0.4 * 0.4 * 0.9),
         (7,  0.4 * 0.6 * 0.1 * 2),
         (8,  0.4 * 0.6 * 0.9 * 2),
         (9,  0.6 * 0.6 * 0.1),
         (10, 0.6 * 0.6 * 0.9)]
  return reportKnownDiscrete(ans, predictions)

@statisticalTest
def testMem3(seed):
  # Same as testMem3 but with booby traps
  ripl = get_ripl(seed=seed)
  ripl.assume("f","(mem (lambda (arg) (categorical (simplex 0.4 0.6) (array 1 2))))")
  ripl.assume("g","((lambda () (mem (lambda (y) (f (add y 1))))))")
  ripl.assume("x","(f ((if (bernoulli 0.5) (lambda () 1) (lambda () 1))))")
  ripl.assume("y","(g ((lambda () 0)))")
  ripl.assume("w","((lambda () (f 2)))")
  ripl.assume("z","(g 1)")
  ripl.assume("q","(categorical (simplex 0.1 0.9) (array 1 2))")
  ripl.predict('(add x y w z q)',label="pid")

  predictions = collectSamples(ripl,"pid")
  ans = [(5,  0.4 * 0.4 * 0.1),
         (6,  0.4 * 0.4 * 0.9),
         (7,  0.4 * 0.6 * 0.1 * 2),
         (8,  0.4 * 0.6 * 0.9 * 2),
         (9,  0.6 * 0.6 * 0.1),
         (10, 0.6 * 0.6 * 0.9)]
  return reportKnownDiscrete(ans, predictions)

@on_inf_prim("mh")
def testMem4():
  # Like TestMem1, makes sure that MSPs handle changes to their
  # arguments without crashing
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

@statisticalTest
def testMemArray(seed):
  # Same as testMem2 but when the arguments are arrays
  ripl = get_ripl(seed=seed)
  ripl.assume("f","(mem (lambda (arg) (categorical (simplex 0.4 0.6) (array 1 2))))")
  ripl.assume("x","(f (array 1 2))")
  ripl.assume("y","(f (array 1 2))")
  ripl.assume("w","(f (array 3 4))")
  ripl.assume("z","(f (array 3 4))")
  ripl.assume("q","(categorical (simplex 0.1 0.9) (array 1 2))")
  ripl.predict('(add x y w z q)',label="pid")

  predictions = collectSamples(ripl,"pid")
  ans = [(5,  0.4 * 0.4 * 0.1),
         (6,  0.4 * 0.4 * 0.9),
         (7,  0.4 * 0.6 * 0.1 * 2),
         (8,  0.4 * 0.6 * 0.9 * 2),
         (9,  0.6 * 0.6 * 0.1),
         (10, 0.6 * 0.6 * 0.9)]
  return reportKnownDiscrete(ans, predictions)

@statisticalTest
def testMemSP(seed):
  # Same as testMem2 but when the arguments are SPs
  ripl = get_ripl(seed=seed)
  ripl.assume("f","(mem (lambda (arg) (categorical (simplex 0.4 0.6) (array 1 2))))")
  ripl.assume("g","(lambda (x) x)")
  ripl.assume("h","(lambda (x) 1)")
  ripl.assume("x","(f g)")
  ripl.assume("y","(f g)")
  ripl.assume("w","(f h)")
  ripl.assume("z","(f h)")
  ripl.assume("q","(categorical (simplex 0.1 0.9) (array 1 2))")
  ripl.predict('(add x y w z q)',label="pid")

  predictions = collectSamples(ripl,"pid")
  ans = [(5,  0.4 * 0.4 * 0.1),
         (6,  0.4 * 0.4 * 0.9),
         (7,  0.4 * 0.6 * 0.1 * 2),
         (8,  0.4 * 0.6 * 0.9 * 2),
         (9,  0.6 * 0.6 * 0.1),
         (10, 0.6 * 0.6 * 0.9)]
  return reportKnownDiscrete(ans, predictions)

############ Puma mem tests

def testMemoizingOnAList1():
  # MSP.requestPSP.simulate() needs to quote the values to pass this.
  # In Puma, VentureList needs to override several VentureValue
  # methods as well
  ripl = get_ripl()
  ripl.assume("f","(mem (lambda (x) (if (flip) 1 1)))")
  ripl.predict("(f (list 0))",label="pid")
  predictions = collectSamples(ripl,"pid",3)
  assert predictions == [1, 1, 1]

def testMemoizingOnASymbol1():
  # MSP.requestPSP.simulate() needs to quote the values to pass this.
  # In Puma, VentureSymbol needs to override several VentureValue
  # methods as well
  ripl = get_ripl()
  ripl.assume("f","(mem (lambda (x) (if (flip) 1 1)))")
  ripl.predict("(f (quote sym))",label="pid")
  predictions = collectSamples(ripl,"pid",3)
  assert predictions == [1, 1, 1]

def testForgetMem():
  ripl = get_ripl()
  ripl.assume("f","(mem (lambda () (normal 0 1)))")
  a = ripl.predict("(f)", label="p1")
  b = ripl.predict("(f)", label="p2")
  assert a == b
  ripl.forget("p1")
  ripl.forget("p2")
  c = ripl.predict("(f)", label="p3")
  assert a != c

def testMemLoop():
  ripl = get_ripl()
  ripl.assume("f","(mem (lambda () (if (flip) (+ 1 (f)) 0)))")
  with assert_raises_regexp(
      Exception, 'mem argument loop|request at existing address'):
    for _ in range(50):
      ripl.sample("(f)")

# TODO slow to run, and not worth it 
def testMemHashCollisions1():
  # For large A and B, makes sure that MSPs don't allow hash
  # collisions for requests based on different arguments.
  from nose import SkipTest
  raise SkipTest("Skipping testMemHashCollisions1.  Issue https://app.asana.com/0/9277419963067/9801332616438")
  ripl = get_ripl()
  ripl.assume("f","(mem (lambda (a b) (normal 0.0 1.0)))")
  for a in range(1000):
    for b in range(1000):
      ripl.observe("(f %d %d)" % (a,b),"0.5")
