import math
import scipy.stats as stats
from nose import SkipTest

from venture.test.stats import statisticalTest, reportKnownContinuous, reportKnownMeanVariance, reportKnownDiscrete
from venture.test.config import get_ripl, collectSamples, collect_iid_samples

@statisticalTest
def testNormal1():
  ripl = get_ripl()
  ripl.predict("(normal 0 1)")
  predictions = collectSamples(ripl,1)
  cdf = lambda x: stats.norm.cdf(x,loc=0,scale=1)
  return reportKnownContinuous(cdf, predictions, "N(0,1)")

def testNormal2():
  ripl = get_ripl()
  ripl.predict("(normal (normal 0 1) 1)")
  predictions = collectSamples(ripl,1)

def testNormal3():
  ripl = get_ripl()
  ripl.assume("f","(lambda (mu) (normal mu 1))")
  ripl.predict("(f (normal 0 1))")
  predictions = collectSamples(ripl,1)

def testNormal4():
  ripl = get_ripl()
  ripl.assume("f","(lambda (mu) (normal mu 1))")
  ripl.assume("g","(lambda (x y z) ((lambda () f)))")
  ripl.predict("((g (f (normal 0 1)) (f 5) (f (f 1))) 5)")
  predictions = collectSamples(ripl,1)
