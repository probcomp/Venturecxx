import math
import scipy.stats as stats
from nose import SkipTest
from testconfig import config
from venture.test.stats import statisticalTest, reportKnownContinuous, reportKnownMeanVariance
from venture.test.config import get_ripl, collectSamples

@statisticalTest
def testNormalWithObserve1():
  "Checks the posterior distribution on a Gaussian given an unlikely observation"
  if config["get_ripl"] != "puma": raise SkipTest("Slice only implemented in puma")
  ripl = get_ripl()
  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.observe("(normal a 1.0)", 14.0)
  # Posterior for a is normal with mean 12, precision 2
#  ripl.predict("(normal a 1.0)")

  predictions = collectSamples(ripl,1,infer="(slice default one 50)")
  cdf = stats.norm(loc=12, scale=math.sqrt(0.5)).cdf
  return reportKnownContinuous(cdf, predictions, "N(12,sqrt(1.5))")

@statisticalTest
def testNormalWithObserve2a():
  "Checks the posterior distribution on a Gaussian given an unlikely observation.  The difference between this and 1 is an extra predict, which apparently has a deleterious effect on mixing."
  if config["get_ripl"] != "puma": raise SkipTest("Slice only implemented in puma")
  ripl = get_ripl()
  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.observe("(normal a 1.0)", 14.0)
  # Posterior for a is normal with mean 12, precision 2
  ripl.predict("(normal a 1.0)")

  predictions = collectSamples(ripl,1,infer="(slice default one 50)")
  cdf = stats.norm(loc=12, scale=math.sqrt(0.5)).cdf
  return reportKnownContinuous(cdf, predictions, "N(12,sqrt(0.5))")

@statisticalTest
def testNormalWithObserve2b():
  "Checks the posterior distribution on a Gaussian given an unlikely observation"
  if config["get_ripl"] != "puma": raise SkipTest("Slice only implemented in puma")  
  ripl = get_ripl()
  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.observe("(normal a 1.0)", 14.0)
  # Posterior for a is normal with mean 12, precision 2
  ripl.predict("(normal a 1.0)")

  predictions = collectSamples(ripl,3,infer="(slice default one 50)")
  cdf = stats.norm(loc=12, scale=math.sqrt(1.5)).cdf
  return reportKnownContinuous(cdf, predictions, "N(12,sqrt(1.5))")

@statisticalTest
def testStudentT1():
  "Simple program involving simulating from a student_t"
  if config["get_ripl"] != "puma": raise SkipTest("Slice only implemented in puma")  
  ripl = get_ripl()
  ripl.assume("a", "(student_t 1.0)")
  ripl.observe("(normal a 1.0)", 3.0)
  predictions = collectSamples(ripl,1,infer="(slice default one 50)")

  # Posterior of a is proprtional to
  def postprop(a):
    return stats.t(1).pdf(a) * stats.norm(loc=3).pdf(a)
  import scipy.integrate as integrate
  (normalize,_) = integrate.quad(postprop, -10, 10)
  def posterior(a): return postprop(a) / normalize
  (meana,_) = integrate.quad(lambda x: x * posterior(x), -10, 10)
  (meanasq,_) = integrate.quad(lambda x: x * x * posterior(x), -10, 10)
  vara = meanasq - meana * meana
  return reportKnownMeanVariance(meana, vara, predictions)

@statisticalTest
def testStudentT2():
  "Simple program involving simulating from a student_t"
  if config["get_ripl"] != "puma": raise SkipTest("Slice only implemented in puma")  
  ripl = get_ripl()
  ripl.assume("a", "(student_t 1.0)")
  ripl.observe("(normal a 1.0)", 3.0)
  ripl.predict("(normal a 1.0)")
  predictions = collectSamples(ripl,3,infer="(slice default one 50)")

  # Posterior of a is proprtional to
  def postprop(a):
    return stats.t(1).pdf(a) * stats.norm(loc=3).pdf(a)
  import scipy.integrate as integrate
  (normalize,_) = integrate.quad(postprop, -10, 10)
  def posterior(a): return postprop(a) / normalize
  (meana,_) = integrate.quad(lambda x: x * posterior(x), -10, 10)
  (meanasq,_) = integrate.quad(lambda x: x * x * posterior(x), -10, 10)
  vara = meanasq - meana * meana
  return reportKnownMeanVariance(meana, vara + 1.0, predictions)


