from venture.shortcuts import *
from stat_helpers import *
from test_globals import N, globalKernel

def RIPL(): return make_lite_church_prime_ripl()

def testVentureNormalHMM1(N):
  ripl = RIPL()
  ripl.assume("f","""
(mem (lambda (i)
  (if (eq i 0)
    (normal 0.0 1.0)
    (normal (f (minus i 1)) 1.0))))
""")
  ripl.assume("g","""
(mem (lambda (i)
  (normal (f i) 1.0)))
""")
  # Solution by forward algorithm inline
  # p((f 0))           = normal mean      0, var     1, prec 1
  # p((g 0) | (f 0))   = normal mean  (f 0), var     1, prec 1
  ripl.observe("(g 0)",1.0)
  # p((f 0) | history) = normal mean    1/2, var   1/2, prec 2
  # p((f 1) | history) = normal mean    1/2, var   3/2, prec 2/3
  # p((g 1) | (f 1))   = normal mean  (f 1), var     1, prec 1
  ripl.observe("(g 1)",2.0)
  # p((f 1) | history) = normal mean    7/5, var   3/5, prec 5/3
  # p((f 2) | history) = normal mean    7/5, var   8/5, prec 5/8
  # p((g 2) | (f 2))   = normal mean  (f 2), var     1, prec 1
  ripl.observe("(g 2)",3.0)
  # p((f 2) | history) = normal mean  31/13, var  8/13, prec 13/8
  # p((f 3) | history) = normal mean  31/13, var 21/13, prec 13/21
  # p((g 3) | (f 3))   = normal mean  (f 3), var     1, prec 1
  ripl.observe("(g 3)",4.0)
  # p((f 3) | history) = normal mean 115/34, var 21/34, prec 34/21
  # p((f 4) | history) = normal mean 115/34, var 55/34, prec 34/55
  # p((g 4) | (f 4))   = normal mean  (f 4), var     1, prec 1
  ripl.observe("(g 4)",5.0)
  # p((f 4) | history) = normal mean 390/89, var 55/89, prec 89/55
  ripl.predict("(f 4)")

  predictions = collectSamples(ripl,8,N)
  reportKnownMeanVariance("TestVentureNormalHMM1", 390/89.0, 55/89.0, predictions)
  cdf = stats.norm(loc=390/89.0, scale=math.sqrt(55/89.0)).cdf
  return reportKnownContinuous("TestVentureHMM1", cdf, predictions, "N(4.382, 0.786)")

def testVentureBinaryHMM1():
  ripl = RIPL()
  ripl.assume("f","""
(mem (lambda (i)
  (if (eq i 0)
    (bernoulli 0.5)
    (if (f (minus i 1))
      (bernoulli 0.7)
      (bernoulli 0.3)))))
""")

  ripl.assume("g","""
(mem (lambda (i)
  (if (f i)
    (bernoulli 0.8)
    (bernoulli 0.1))))
""")

  ripl.observe("(g 1)",False)
  ripl.observe("(g 2)",False)
  ripl.observe("(g 3)",True)
  ripl.observe("(g 4)",False)
  ripl.observe("(g 5)",False)
  ripl.predict("(list (f 0) (f 1) (f 2) (f 3) (f 4) (f 5))")

  predictions = collectSamples(ripl,8,N)
  sums = [0 for i in range(6)]
  for p in predictions: sums = [sums[i] + p[i] for i in range(6)]
  ps = [.3531,.1327,.1796,.6925,.1796,.1327]
  eps = [float(x) / N for x in sums] if N > 0 else [0 for x in sums]
  printTest("TestVentureBinaryHMM1 (mixes terribly)",ps,eps)
  return reportPassage("TestVentureBinaryHMM1")
