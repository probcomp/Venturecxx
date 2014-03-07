from venture.test.stats import statisticalTest, reportKnownContinuous, reportKnownMeanVariance, reportKnownDiscrete
from venture.test.config import get_ripl, collectSamples, collect_iid_samples, defaultKernel
import math
import scipy.stats as stats
from nose import SkipTest
from testconfig import config

@statisticalTest
def testSliceBasic1():
  "Basic sanity test for slice"
  if config["get_ripl"] != "lite": raise SkipTest("Slice only implemented in lite")
  ripl = get_ripl()
  ripl.assume("a", "(normal 10.0 1.0)",label="pid")
  predictions = collectSamples(ripl,"pid",infer_merge={"kernel":"slice"})
  cdf = stats.norm(loc=10, scale=1).cdf
  return reportKnownContinuous(cdf, predictions, "N(10,1.0))")

@statisticalTest
def testSliceNormalWithObserve1():
  if config["get_ripl"] != "lite": raise SkipTest("Slice only implemented in lite")
  "Checks the posterior distribution on a Gaussian given an unlikely observation"
  ripl = get_ripl()
  ripl.assume("a", "(normal 10.0 1.0)",label="pid")
  ripl.observe("(normal a 1.0)", 14.0)
  # Posterior for a is normal with mean 12, precision 2
#  ripl.predict("(normal a 1.0)")

  predictions = collectSamples(ripl,"pid",infer_merge={"kernel":"slice"})
  cdf = stats.norm(loc=12, scale=math.sqrt(0.5)).cdf
  return reportKnownContinuous(cdf, predictions, "N(12,sqrt(1.5))")
