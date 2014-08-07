from nose import SkipTest
from venture.test.stats import statisticalTest, reportKnownDiscrete
from venture.test.config import get_ripl, collectSamples, skipWhenRejectionSampling, rejectionSampling

def testMakeBetaBernoulli1():
  for maker in ["make_beta_bernoulli","make_uc_beta_bernoulli"]:
    for hyper in ["10.0", "(normal 10.0 1.0)"]:
      yield checkMakeBetaBernoulli1, maker, hyper

@statisticalTest
def checkMakeBetaBernoulli1(maker, hyper):
  if rejectionSampling() and maker == "make_beta_bernoulli" and hyper == "(normal 10.0 1.0)":
    raise SkipTest("Is the log density of counts bounded for collapsed beta bernoulli?  Issue: https://app.asana.com/0/9277419963067/10623454782852")
  ripl = get_ripl()

  ripl.assume("a", hyper)
  ripl.assume("f", "(%s a a)" % maker)
  ripl.predict("(f)", label="pid")

  for _ in range(20): ripl.observe("(f)", "true")

  predictions = collectSamples(ripl,"pid")
  ans = [(False,.25), (True,.75)]
  return reportKnownDiscrete(ans, predictions)

def testMakeBetaBernoulli2():
  for maker in ["make_beta_bernoulli","make_uc_beta_bernoulli"]:
    yield checkMakeBetaBernoulli2,maker

# These three represent mechanisable ways of fuzzing a program for
# testing language feature interactions (in this case AAA with
# constraint forwarding and brush).
@statisticalTest
def checkMakeBetaBernoulli2(maker):
  if rejectionSampling() and maker == "make_beta_bernoulli":
    raise SkipTest("Is the log density of counts bounded for collapsed beta bernoulli?  Issue: https://app.asana.com/0/9277419963067/10623454782852")
  ripl = get_ripl()

  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "((lambda () (%s ((lambda () a)) ((lambda () a)))))" % maker)
  ripl.predict("(f)", label="pid")

  for _ in range(20): ripl.observe("((lambda () (f)))", "true")

  predictions = collectSamples(ripl,"pid")
  ans = [(False,.25), (True,.75)]
  return reportKnownDiscrete(ans, predictions)

def testMakeBetaBernoulli3():
  for maker in ["make_beta_bernoulli","make_uc_beta_bernoulli"]:
    yield checkMakeBetaBernoulli3,maker

@skipWhenRejectionSampling("Rejection sampling doesn't work when resimulations of unknown code are observed")
@statisticalTest
def checkMakeBetaBernoulli3(maker):
  ripl = get_ripl()

  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "(%s a a)" % maker)
  ripl.predict("(f)", label="pid")

  for _ in range(10): ripl.observe("(f)", "true")
  for _ in range(10): ripl.observe("""
(if (lt a 10.0)
  (f)
  (f))""", "true")

  predictions = collectSamples(ripl,"pid")
  ans = [(False,.25), (True,.75)]
  return reportKnownDiscrete(ans, predictions)

def testMakeBetaBernoulli4():
  for maker in ["make_beta_bernoulli","make_uc_beta_bernoulli"]:
    yield checkMakeBetaBernoulli4,maker

@skipWhenRejectionSampling("Rejection sampling doesn't work when resimulations of unknown code are observed")
@statisticalTest
def checkMakeBetaBernoulli4(maker):
  ripl = get_ripl()

  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", """
(if (lt a 10.0)
  ({0} a a)
  ({0} a a))""".format(maker))
  ripl.predict("(f)", label="pid")

  for _ in range(20): ripl.observe("(f)", "true")

  predictions = collectSamples(ripl,"pid")
  ans = [(False,.25), (True,.75)]
  return reportKnownDiscrete(ans, predictions)


##### (3) Staleness

# This section should not hope to find staleness, since all backends should
# assert that a makerNode has been regenerated before applying it.
# Therefore this section should try to trigger that assertion.

