import math
import scipy.stats as stats
from nose import SkipTest
from testconfig import config
from venture.test.stats import statisticalTest, reportKnownContinuous
from venture.test.config import get_ripl, collectSamples

@statisticalTest
def testNormalWithObserve1():
  "Checks the posterior distribution on a Gaussian given an unlikely observation"
  if config["get_ripl"] != "lite": raise SkipTest("HMC only implemented in Lite")
  ripl = get_ripl()
  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.observe("(normal a 1.0)", 14.0)
  # Posterior for a is normal with mean 12, precision 2
#  ripl.predict("(normal a 1.0)")

  predictions = collectSamples(ripl,1,infer="(hmc default one 0.05 20 10)")
  cdf = stats.norm(loc=12, scale=math.sqrt(0.5)).cdf
  return reportKnownContinuous(cdf, predictions, "N(12,sqrt(0.5))")

def testMVGaussSmoke():
  """Confirm that projecting a multivariate Gaussian to one dimension
  results in a univariate Gaussian."""
  ripl = get_ripl()
  ripl.assume("vec", "(multivariate_normal (array 1 2) (matrix (list (list 1 2) (list 2 1))))")
  ripl.infer("(hmc default all 0.01 20 2)")

def testMoreElaborate():
  """Confirm that HMC still works in the presence of brush.  Do not,
  however, mess with the possibility that the principal nodes that HMC
  operates over may themselves be in the brush."""
  ripl = get_ripl()
  ripl.assume("x", "(scope_include (quote param) 0 (uniform_continuous -10 10))")
  ripl.assume("y", "(scope_include (quote param) 1 (uniform_continuous -10 10))")
  ripl.assume("out", """
(if (< x 0)
    (multivariate_normal (array x y) (matrix (list (list 1 3) (list 3 1))))
    (multivariate_normal (array x y) (matrix (list (list 3 0) (list 0 3)))))
""")
  # TODO Unexpectedly serious problem: how to observe a data structure?
  # Can't observe coordinatewise because observe is not flexible
  # enough.  For this to work we would need observations of splits.
  # ripl.observe("(lookup out 0)", 0)
  # ripl.observe("(lookup out 1)", 0)
  # Can't observe through the ripl literally because the string
  # substitution (!) is not flexible enough.
  # ripl.observe("out", [0, 0])
  v = [{"type": "real", "value": 0}, {"type": "real", "value": 0}]
  ripl.sivm.execute_instruction({"instruction":"observe","expression":"out","value":{"type":"list","value":v}})

  ripl.infer("(hmc param all 0.01 20 2)")
