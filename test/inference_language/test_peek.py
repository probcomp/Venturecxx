import scipy.stats as stats
from venture.test.stats import statisticalTest, reportKnownContinuous
from venture.test.config import get_ripl, default_num_samples

@statisticalTest
def testPeekSmoke1():
  ripl = get_ripl()
  ripl.assume("x", "(normal 0 1)")
  predictions = ripl.infer("(cycle ((mh default one 1) (peek x)) %s)" % default_num_samples())['x']
  cdf = stats.norm(loc=0.0, scale=1.0).cdf
  return reportKnownContinuous(cdf, predictions, "N(0,1)")

@statisticalTest
def testPeekSmoke2():
  ripl = get_ripl()
  predictions = ripl.infer("(cycle ((peek (normal 0 1) x)) %s)" % default_num_samples())['x']
  cdf = stats.norm(loc=0.0, scale=1.0).cdf
  return reportKnownContinuous(cdf, predictions, "N(0,1)")

@statisticalTest
def testPeekAllSmoke1():
  ripl = get_ripl()
  ripl.infer("(resample 2)")
  ripl.assume("x", "(normal 0 1)")
  predictionss = ripl.infer("(cycle ((mh default one 1) (peek_all x)) %s)" % default_num_samples())['x']
  assert len(predictionss) == 2
  cdf = stats.norm(loc=0.0, scale=1.0).cdf
  return reportKnownContinuous(cdf, predictionss[0], "N(0,1)")

@statisticalTest
def testPeekAllSmoke2():
  ripl = get_ripl()
  ripl.infer("(resample 2)")
  predictionss = ripl.infer("(cycle ((peek_all (normal 0 1) x)) %s)" % default_num_samples())['x']
  assert len(predictionss) == 2
  cdf = stats.norm(loc=0.0, scale=1.0).cdf
  return reportKnownContinuous(cdf, predictionss[0], "N(0,1)")
