import math
import scipy.stats as stats
from nose import SkipTest
from venture.test.stats import statisticalTest, reportKnownContinuous, reportKnownMeanVariance
from venture.test.config import get_ripl, collectSamples, defaultKernel, default_num_transitions_per_sample

@statisticalTest
def testSliceBasic1():
  "Basic sanity test for slice"
  if defaultKernel() != "mh":
    raise SkipTest("Tests the Slice kernel, do not repeat for alternative kernels")
  ripl = get_ripl()
  ripl.assume("a", "(normal 10.0 1.0)",label="pid")
  predictions = collectSamples(ripl,"pid",infer="(slice default one %s)" % default_num_transitions_per_sample())
  cdf = stats.norm(loc=10, scale=1).cdf
  return reportKnownContinuous(cdf, predictions, "N(10,1.0))")

@statisticalTest
def testSliceNormalWithObserve1():
  "Checks the posterior distribution on a Gaussian given an unlikely observation"
  if defaultKernel() != "mh":
    raise SkipTest("Tests the Slice kernel, do not repeat for alternative kernels")
  ripl = get_ripl()
  ripl.assume("a", "(normal 10.0 1.0)",label="pid")
  ripl.observe("(normal a 1.0)", 14.0)
  # Posterior for a is normal with mean 12, precision 2
#  ripl.predict("(normal a 1.0)")

  predictions = collectSamples(ripl,"pid",infer="(slice default one %s)" % default_num_transitions_per_sample())
  cdf = stats.norm(loc=12, scale=math.sqrt(0.5)).cdf
  return reportKnownContinuous(cdf, predictions, "N(12,sqrt(0.5))")

@statisticalTest
def testSliceNormalWithObserve2a():
  "Checks the posterior distribution on a Gaussian given an unlikely observation.  The difference between this and 1 is an extra predict, which apparently has a deleterious effect on mixing."
  if defaultKernel() != "mh":
    raise SkipTest("Tests the Slice kernel, do not repeat for alternative kernels")
  ripl = get_ripl()
  ripl.assume("a", "(normal 10.0 1.0)", label="pid")
  ripl.observe("(normal a 1.0)", 14.0)
  # Posterior for a is normal with mean 12, precision 2
  ripl.predict("(normal a 1.0)")

  predictions = collectSamples(ripl,"pid",infer="(slice default one %s)" % default_num_transitions_per_sample())
  cdf = stats.norm(loc=12, scale=math.sqrt(0.5)).cdf
  return reportKnownContinuous(cdf, predictions, "N(12,sqrt(0.5))")

@statisticalTest
def testSliceNormalWithObserve2b():
  "Checks the posterior distribution on a Gaussian given an unlikely observation"
  if defaultKernel() != "mh":
    raise SkipTest("Tests the Slice kernel, do not repeat for alternative kernels")
  ripl = get_ripl()
  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.observe("(normal a 1.0)", 14.0)
  # Posterior for a is normal with mean 12, precision 2
  ripl.predict("(normal a 1.0)", label="pid")

  predictions = collectSamples(ripl,"pid",infer="(slice default one %s)" % default_num_transitions_per_sample())
  cdf = stats.norm(loc=12, scale=math.sqrt(1.5)).cdf
  return reportKnownContinuous(cdf, predictions, "N(12,sqrt(1.5))")

@statisticalTest
def testSliceStudentT1():
  "Simple program involving simulating from a student_t"
  if defaultKernel() != "mh":
    raise SkipTest("Tests the Slice kernel, do not repeat for alternative kernels")
  ripl = get_ripl()
  ripl.assume("a", "(student_t 1.0)", label="pid")
  ripl.observe("(normal a 1.0)", 3.0)
  predictions = collectSamples(ripl,"pid",infer="(slice default one %s)" % default_num_transitions_per_sample())

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
def testSliceStudentT2():
  "Simple program involving simulating from a student_t"
  if defaultKernel() != "mh":
    raise SkipTest("Tests the Slice kernel, do not repeat for alternative kernels")
  ripl = get_ripl()
  ripl.assume("a", "(student_t 1.0)")
  ripl.observe("(normal a 1.0)", 3.0)
  ripl.predict("(normal a 1.0)", label="pid")
  predictions = collectSamples(ripl,"pid",infer="(slice default one %s)" % (default_num_transitions_per_sample() * 4))

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
