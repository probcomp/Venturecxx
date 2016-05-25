from nose import SkipTest
from testconfig import config

from venture.test.config import get_ripl
from venture.test.config import collectSamples
from venture.test.stats import statisticalTest, reportKnownDiscrete

@statisticalTest
def testSuffCat1a():
  if config['get_ripl'] != 'mite':
    raise SkipTest("dpmem only exists in mite")

  ripl = get_ripl()

  ripl.assume("f", "(make_suff_cat (symmetric_dirichlet 1 2) (list true false))")
  ripl.observe("(f)", "true")
  ripl.observe("(f)", "true")
  ripl.predict("(f)", label="pid")

  predictions = collectSamples(ripl, "pid")
  ans = [(False, 0.25), (True, 0.75)]
  return reportKnownDiscrete(ans, predictions)

@statisticalTest
def testSuffCat1b():
  if config['get_ripl'] != 'mite':
    raise SkipTest("dpmem only exists in mite")

  ripl = get_ripl()

  ripl.assume("f", "(make_suff_cat (symmetric_dirichlet 1 2) (list true false))")
  ripl.predict("(f)", label="pid")
  ripl.observe("(f)", "true")
  ripl.observe("(f)", "true")

  predictions = collectSamples(ripl, "pid")
  ans = [(False, 0.25), (True, 0.75)]
  return reportKnownDiscrete(ans, predictions)
