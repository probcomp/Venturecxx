from testconfig import config
from nose import SkipTest
from venture.test.stats import statisticalTest, reportKnownDiscrete
from venture.test.config import get_ripl, collectSamples, on_inf_prim
from nose.tools import eq_

@statisticalTest
def testCategorical1():
  "A simple test that checks the interface of categorical and its simulate method"
  ripl = get_ripl()

  ripl.assume("x", "(categorical (simplex 0.1 0.2 0.3 0.4) (array 1 2 3 4))")
  ripl.assume("y", "(categorical (simplex 0.2 0.6 0.2) (array 1 2 3))")
  ripl.predict("(+ x y)",label="pid")

  predictions = collectSamples(ripl,"pid")
  ans = [(2, 0.1 * 0.2),
         (3, 0.1 * 0.6 + 0.2 * 0.2),
         (4, 0.1 * 0.2 + 0.2 * 0.6 + 0.3 * 0.2),
         (5, 0.2 * 0.2 + 0.3 * 0.6 + 0.4 * 0.2),
         (6, 0.3 * 0.2 + 0.4 * 0.6),
         (7, 0.4 * 0.2)]
  return reportKnownDiscrete(ans, predictions)

@statisticalTest
def testCategoricalAbsorb():
  "A simple test that checks the interface of categorical and its simulate and log density methods"
  ripl = get_ripl()

  ripl.assume("x","(simplex .1 .9)")
  ripl.assume("y","(simplex .55 .45)")
  ripl.assume("b","(flip)",label="b")
  ripl.observe("(categorical (if b x y) (array 10 100))","100")

  predictions = collectSamples(ripl,"b")
  ans = [(False,0.333),(True,0.667)]
  return reportKnownDiscrete(ans, predictions)

@on_inf_prim("none")
def testCategoricalDefault1():
  eq_(get_ripl().predict("(categorical (simplex 1))"), 0)

@statisticalTest
def testLogCategoricalAbsorb():
  "A simple test that checks the interface of log categorical and its simulate and log density methods"
  if config["get_ripl"] != "puma":
    raise SkipTest("log categorical only implemented in Puma")
  ripl = get_ripl()

  ripl.assume("x","(simplex (log .1) (log .9))")
  ripl.assume("y","(simplex (log .55) (log .45))")
  ripl.assume("b","(flip)",label="b")
  ripl.observe("(log_categorical (if b x y) (array 10 100))","100")

  predictions = collectSamples(ripl,"b")
  ans = [(False,0.333),(True,0.667)]
  return reportKnownDiscrete(ans, predictions)
