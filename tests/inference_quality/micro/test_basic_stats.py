from venture.shortcuts import *
from stat_helpers import *
from test_globals import N, globalKernel

def RIPL(): return make_lite_church_prime_ripl()

def testBernoulliIfNormal1():
  "A simple program with bernoulli, if, and normal applications in the brush"
  ripl = RIPL()
  ripl.assume("b", "(bernoulli 0.3)")
  ripl.predict("(if b (normal 0.0 1.0) (normal 10.0 1.0))")
  predictions = collectSamples(ripl,2,N)
  cdf = lambda x: 0.3 * stats.norm.cdf(x,loc=0,scale=1) + 0.7 * stats.norm.cdf(x,loc=10,scale=1)
  return reportTest(reportKnownContinuous("TestBernoulli1", cdf, predictions, "0.7*N(0,1) + 0.3*N(10,1)"))

def testBernoulliIfNormal2():
  "A simple program with bernoulli, if, and an absorbing application of normal"
  ripl = RIPL()
  ripl.assume("b", "(bernoulli 0.3)")
  ripl.predict("(normal (if b 0.0 10.0) 1.0)")
  predictions = collectSamples(ripl,2,N)
  cdf = lambda x: 0.3 * stats.norm.cdf(x,loc=0,scale=1) + 0.7 * stats.norm.cdf(x,loc=10,scale=1)
  return reportTest(reportKnownContinuous("TestBernoulli2", cdf, predictions, "0.7*N(0,1) + 0.3*N(10,1)"))

def testNormalWithObserve1():
  "Checks the posterior distribution on a Gaussian given an unlikely observation"
  ripl = RIPL()
  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.observe("(normal a 1.0)", 14.0)
  # Posterior for a is normal with mean 12, precision 2
  ripl.predict("(normal a 1.0)")

  predictions = collectSamples(ripl,3,N)
  cdf = stats.norm(loc=12, scale=math.sqrt(1.5)).cdf
  return reportKnownContinuous("testMHNormal0", cdf, predictions, "N(12,sqrt(1.5))")

def testNormalWithObserve2():
  "Checks the posterior of a Gaussian in a Linear-Gaussian-BN"
  ripl = RIPL()
  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("b", "(normal a 1.0)")
  # Prior for b is normal with mean 10, variance 2 (precision 1/2)
  ripl.observe("(normal b 1.0)", 14.0)
  # Posterior for b is normal with mean 38/3, precision 3/2 (variance 2/3)
  # Likelihood of a is normal with mean 0, variance 2 (precision 1/2)
  # Posterior for a is normal with mean 34/3, precision 3/2 (variance 2/3)
  ripl.predict("""
(if (lt a 100.0)
  (normal (plus a b) 1.0)
  (normal (times a b) 1.0))
""")

  predictions = collectSamples(ripl,4,N)
  # Unfortunately, a and b are (anti?)correlated now, so the true
  # distribution of the sum is mysterious to me
  cdf = stats.norm(loc=24, scale=math.sqrt(7.0/3.0)).cdf
  return reportKnownContinuous("testMHNormal1", cdf, predictions, "approximately N(24,sqrt(7/3))")

def testStudentT1():
  "Simple program involving simulating from a student_t"
  ripl = RIPL()
  ripl.assume("a", "(student_t 1.0)")
  ripl.observe("(normal a 1.0)", 3.0)
  ripl.predict("(normal a 1.0)")
  predictions = collectSamples(ripl,3,N)

  # Posterior of a is proprtional to
  def postprop(a):
    return stats.t(1).pdf(a) * stats.norm(loc=3).pdf(a)
  import scipy.integrate as int
  (normalize,_) = int.quad(postprop, -10, 10)
  def posterior(a): return postprop(a) / normalize
  (meana,_) = int.quad(lambda x: x * posterior(x), -10, 10)
  (meanasq,_) = int.quad(lambda x: x * x * posterior(x), -10, 10)
  vara = meanasq - meana * meana
  return reportKnownMeanVariance("TestStudentT0", meana, vara + 1.0, predictions)


def testSprinkler1():
  "Classic Bayes-net example, with no absorbing when proposing to 'rain'"
  ripl = RIPL()
  ripl.assume("rain","(bernoulli 0.2)")
  ripl.assume("sprinkler","(if rain (bernoulli 0.01) (bernoulli 0.4))")
  ripl.assume("grassWet","""
(if rain
  (if sprinkler (bernoulli 0.99) (bernoulli 0.8))
  (if sprinkler (bernoulli 0.9)  (bernoulli 0.00001)))
""")
  ripl.observe("grassWet", True)

  predictions = collectSamples(ripl,1,N)
  ans = [(True, .3577), (False, .6433)]
  return reportKnownDiscrete("TestSprinkler1", ans, predictions)

def testSprinkler2():
  "Classic Bayes-net example, absorbing at 'sprinkler' when proposing to 'rain'"
  # this test needs more iterations than most others, because it mixes badly

  ripl = RIPL()
  ripl.assume("rain","(bernoulli 0.2)")
  ripl.assume("sprinkler","(bernoulli (if rain 0.01 0.4))")
  ripl.assume("grassWet","""
(bernoulli
 (if rain
   (if sprinkler 0.99 0.8)
   (if sprinkler 0.9 0.00001)))
""")
  ripl.observe("grassWet", True)

  predictions = collectSamples(ripl,1,N)
  ans = [(True, .3577), (False, .6433)]
  return reportKnownDiscrete("TestSprinkler2 (mixes terribly)", ans, predictions)

def testBLOGCSI1():
  "Context-sensitive Bayes-net taken from BLOG examples"
  ripl = RIPL()
  ripl.assume("u","(bernoulli 0.3)")
  ripl.assume("v","(bernoulli 0.9)")
  ripl.assume("w","(bernoulli 0.1)")
  ripl.assume("getParam","(lambda (z) (if z 0.8 0.2))")
  ripl.assume("x","(bernoulli (if u (getParam w) (getParam v)))")

  predictions = collectSamples(ripl,5,N)
  ans = [(True, .596), (False, .404)]
  return reportKnownDiscrete("TestBLOGCSI1", ans, predictions)

def testGeometric1(N):
  ripl = RIPL()
  ripl.assume("alpha1","(gamma 5.0 2.0)")
  ripl.assume("alpha2","(gamma 5.0 2.0)")
  ripl.assume("p", "(beta alpha1 alpha2)")
  ripl.assume("geo","(lambda (p) (branch (bernoulli p) (lambda () 1) (lambda () (plus 1 (geo p)))))")
  ripl.predict("(geo p)",label="pid")

  predictions = collectSamples(ripl,"pid",N)

  k = 128
  ans = [(n,math.pow(2,-n)) for n in range(1,k)]
  return reportKnownDiscrete("TestGeometric1", ans, predictions)

def testTrig1(N):
  ripl = RIPL()
  ripl.assume("sq","(lambda (x) (* x x))")
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("a","(sq (sin x))")
  ripl.assume("b","(sq (cos x))")
  ripl.predict("(+ a b)")
  for i in range(N/10):
    ripl.infer(10)
    assert abs(ripl.report(5) - 1) < .001
  return reportPassage("TestTrig1")
