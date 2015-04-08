import scipy.stats
from nose.tools import assert_equal, assert_almost_equal

from venture.test.stats import statisticalTest, reportKnownDiscrete
from venture.test.config import get_ripl, collectSamples, default_num_transitions_per_sample, on_inf_prim, broken_in

@statisticalTest
def testBinomial1():
  "A simple test that checks the interface of binomial and its simulate method"
  ripl = get_ripl()

  p = 0.3
  n = 4
  ripl.assume("p","(if (flip) %f %f)" % (p,p))
  ripl.predict("(binomial %d p)" % n,label="pid")

  predictions = collectSamples(ripl,"pid")
  ans = [(x,scipy.stats.binom.pmf(x,n,p)) for x in range(n+1)]
  assert_almost_equal(sum([xx[1] for xx in ans]),1)
  return reportKnownDiscrete(ans, predictions)

@statisticalTest
def testBinomial2():
  "A simple test that checks the binomial logdensity"
  ripl = get_ripl()

  b = 0.7
  p1 = 0.3
  p2 = 0.4
  n = 4
  ripl.assume("p","(if (flip %f) %f %f)" % (b,p1,p2))
  ripl.predict("(binomial %d p)" % n,label="pid")

  predictions = collectSamples(ripl,"pid")
  ans = [(x,b * scipy.stats.binom.pmf(x,n,p1) + (1 - b) * scipy.stats.binom.pmf(x,n,p2)) for x in range(n+1)]
  assert_almost_equal(sum([xx[1] for xx in ans]),1)
  return reportKnownDiscrete(ans, predictions)

@statisticalTest
@broken_in("puma", "Puma is missing an enumerate method here")
@on_inf_prim("gibbs") # Also MH, but really testing gibbs
def testBinomial3():
  "A simple test that checks the binomial enumerate method"
  ripl = get_ripl()

  b = 0.7
  p1 = 0.3
  p2 = 0.4
  n = 4
  ripl.assume("p","(tag 0 1 (if (flip %f) %f %f))" % (b,p1,p2))
  ripl.predict("(tag 0 0 (binomial %d p))" % n,label="pid")

  predictions = collectSamples(ripl,"pid",infer="(repeat %s (do (mh 0 1 1) (gibbs 0 0 1)))" % default_num_transitions_per_sample())

  ans = [(x,b * scipy.stats.binom.pmf(x,n,p1) + (1 - b) * scipy.stats.binom.pmf(x,n,p2)) for x in range(n+1)]
  assert_almost_equal(sum([xx[1] for xx in ans]),1)
  return reportKnownDiscrete(ans, predictions)
