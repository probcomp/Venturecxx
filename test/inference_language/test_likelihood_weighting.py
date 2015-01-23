import math
import scipy.stats as stats
from nose.tools import assert_almost_equal
from nose import SkipTest

from venture.test.stats import statisticalTest, reportKnownContinuous
from venture.test.config import get_ripl, default_num_samples

@statisticalTest
def testNormalWithObserve1():
  "Checks the posterior distribution on a Gaussian given an unlikely observation"
  ripl = get_ripl()
  ripl.assume("a", "(normal 10.0 1.0)", label="pid")
  ripl.observe("(normal a 1.0)", 14.0)
  # Posterior for a is normal with mean 12, precision 2

  (samples, weights) = collectLikelihoodWeighted(ripl,"pid")
  for (s, w) in zip(samples, weights):
    # The weights I have should be deterministically given by the likelihood
    assert_almost_equal(math.exp(w), stats.norm(loc=14, scale=1).pdf(s))
  prior = stats.norm(loc=10, scale=1).cdf
  # The test points should be drawn from the prior
  return reportKnownContinuous(prior, samples, "N(10,1)")

def collectLikelihoodWeighted(ripl, address):
  vs = []
  wts = []
  for _ in range(default_num_samples()):
    ripl.infer("(likelihood_weight)")
    vs.append(ripl.report(address))
    wts.append(ripl.sivm.core_sivm.engine.trace_handler.log_weights[0])
  return (vs, wts)

def testMultiprocessing():
  "Checking for a strange but in likelihood_weight when using parallel particles"
  raise SkipTest("Currently broken. See asana issue https://app.asana.com/0/9277420529946/24666934712712")
  ripl = get_ripl()
  ripl.infer('(resample_multiprocess 2)')
  ripl.assume('x', '(normal 0 1)')
  ripl.observe('(normal x 1)', 5)
  ripl.infer('(likelihood_weight)')
  log_weights = ripl.sivm.core_sivm.engine.trace_handler.log_weights
  assert log_weights[0] != 0
