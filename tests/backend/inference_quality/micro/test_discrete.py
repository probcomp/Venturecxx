from venture.shortcuts import *
from stat_helpers import *

N = 50
globalKernel = "mh";

def RIPL(): return make_lite_church_prime_ripl()

# Supposed to always fail. Only here to show what error reporting looks like.
def testBernoulli0():
  ripl = RIPL()
  ripl.assume("b", "(bernoulli 0.9)")
  ripl.predict("(if b (normal 0.0 1.0) (normal 10.0 1.0))")
  predictions = collectSamples(ripl,2,N)
  cdf = lambda x: 0.5 * stats.norm.cdf(x,loc=0,scale=1) + 0.5 * stats.norm.cdf(x,loc=10,scale=1)
  return reportTest(reportKnownContinuous("TestBernoulli1", cdf, predictions, "N(0,1) + N(10,1)"))

def testBernoulli1():
  ripl = RIPL()
  ripl.assume("b", "(bernoulli 0.3)")
  ripl.predict("(if b (normal 0.0 1.0) (normal 10.0 1.0))")
  predictions = collectSamples(ripl,2,N)
  cdf = lambda x: 0.5 * stats.norm.cdf(x,loc=0,scale=1) + 0.5 * stats.norm.cdf(x,loc=10,scale=1)
  return reportTest(reportKnownContinuous("TestBernoulli1", cdf, predictions, "N(0,1) + N(10,1)"))

def testBernoulli2():
  ripl = RIPL()
  ripl.assume("b", "(bernoulli 0.3)")
  ripl.predict("(normal (if b 10.0 1.0) 1.0)")
  predictions = collectSamples(ripl,2,N)
  cdf = lambda x: 0.7 * stats.norm.cdf(x,loc=0,scale=1) + 0.3 * stats.norm.cdf(x,loc=10,scale=1)
  return reportTest(reportKnownContinuous("TestBernoulli2", cdf, predictions, "0.7*N(0,1) + 0.3*N(10,1)"))

# Fails currently because:
# 1. Neither backend implement categorical this way yet.
# 2. Neither backend has simplex
# 3. make_vector is used instead of vector
def testCategorical1():
  ripl = RIPL()
  ripl.assume("x", "(categorical (simplex 0.1 0.2 0.3 0.4) (array 1 2 3 4))")
  ripl.assume("y", "(categorical (simplex 0.2 0.6 0.2) (array 1 2 3))")
  ripl.predict("(plus x y)")

  predictions = collectSamples(ripl,3,N)
  ans = [(2, 0.1 * 0.2),
         (3, 0.1 * 0.6 + 0.2 * 0.2),
         (4, 0.1 * 0.2 + 0.2 * 0.6 + 0.3 * 0.2),
         (5, 0.2 * 0.2 + 0.3 * 0.6 + 0.4 * 0.2),
         (6, 0.3 * 0.2 + 0.4 * 0.6),
         (7, 0.4 * 0.2)]
  return reportTest(reportKnownDiscrete("TestCategorical1", ans, predictions))
