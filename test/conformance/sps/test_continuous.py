from nose.tools import eq_
from nose import SkipTest
import scipy.stats as stats
from venture.test.stats import statisticalTest, reportKnownContinuous
from venture.test.config import get_ripl, collectSamples
from testconfig import config

def testMVGaussSmoke():
  if config["get_ripl"] != "lite": raise SkipTest("Multivariate normal only implemented in Lite.  Issue: https://app.asana.com/0/11248128922035/11407880007718")
  eq_(get_ripl().predict("(is_array (multivariate_normal (array 1 2) (matrix (list (list 3 4) (list 4 6)))))"), True)

@statisticalTest
def testMVGaussPrior():
  """Confirm that projecting a multivariate Gaussian to one dimension
  results in a univariate Gaussian."""
  if config["get_ripl"] != "lite": raise SkipTest("Multivariate normal only implemented in Lite.  Issue: https://app.asana.com/0/11248128922035/11407880007718")
  ripl = get_ripl()
  ripl.assume("vec", "(multivariate_normal (array 1 2) (matrix (list (list 1 2) (list 2 1))))")
  ripl.predict("(lookup vec 0)")

  predictions = collectSamples(ripl, 2)
  cdf = stats.norm(loc=1, scale=1).cdf
  return reportKnownContinuous(cdf, predictions, "N(1,1)")
