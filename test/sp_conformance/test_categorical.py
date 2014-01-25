from venture.test.stats import *
from testconfig import config

# Fails currently because:
# 1. Neither backend implement categorical this way yet.
# 2. Neither backend has simplex
# 3. make_vector is used instead of array
@statisticalTest
def testCategorical1():
  "A simple test that checks the interface of categorical and its simulate method"
  ripl = config["get_ripl"]()

  ripl.assume("x", "(categorical (simplex 0.1 0.2 0.3 0.4) (array 1 2 3 4))")
  ripl.assume("y", "(categorical (simplex 0.2 0.6 0.2) (array 1 2 3))")
  ripl.predict("(plus x y)")

  predictions = collectSamples(ripl,3)
  ans = [(2, 0.1 * 0.2),
         (3, 0.1 * 0.6 + 0.2 * 0.2),
         (4, 0.1 * 0.2 + 0.2 * 0.6 + 0.3 * 0.2),
         (5, 0.2 * 0.2 + 0.3 * 0.6 + 0.4 * 0.2),
         (6, 0.3 * 0.2 + 0.4 * 0.6),
         (7, 0.4 * 0.2)]
  return reportKnownDiscrete("TestCategorical1", ans, predictions)
