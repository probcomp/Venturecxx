import math
import scipy.stats as stats
from venture.test.stats import statisticalTest, reportKnownContinuous
from venture.test.config import (get_ripl, collectSamples, gen_on_inf_prim,
                                 gen_broken_in)

@gen_broken_in("puma", "Meanfield not implemented in Puma")
@gen_on_inf_prim("meanfield")
def testMeanFieldBasic():
  tests = (checkMeanFieldBasic1, checkMeanFieldNormalWithObserve1)
  for test in tests: yield test, "(meanfield default one 20 10)"

@statisticalTest
def checkMeanFieldBasic1(infer):
  "Basic sanity test for meanfield"
  ripl = get_ripl()
  ripl.assume("a", "(normal 10.0 1.0)",label="pid")
  predictions = collectSamples(ripl,"pid",infer=infer)
  cdf = stats.norm(loc=10, scale=1).cdf
  return reportKnownContinuous(cdf, predictions, "N(10,1.0))")

@statisticalTest
def checkMeanFieldNormalWithObserve1(infer):
  "Checks the posterior distribution on a Gaussian given an unlikely observation"
  ripl = get_ripl()
  ripl.assume("a", "(normal 10.0 1.0)",label="pid")
  ripl.observe("(normal a 1.0)", 14.0)
  # Posterior for a is normal with mean 12, precision 2
#  ripl.predict("(normal a 1.0)")

  predictions = collectSamples(ripl,"pid",infer=infer)
  cdf = stats.norm(loc=12, scale=math.sqrt(0.5)).cdf
  return reportKnownContinuous(cdf, predictions, "N(12,sqrt(0.5))")
