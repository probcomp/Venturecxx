from venture.test.stats import *
from testconfig import config

def testMakeBetaBernoulli1():
  for maker in ["make_beta_bernoulli","make_uc_beta_bernoulli"]:
    yield checkMakeBetaBernoulli1,maker

@statisticalTest
def checkMakeBetaBernoulli1(maker):
  ripl = config["get_ripl"]()

  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "(%s a a)" % maker)
  ripl.predict("(f)")

  for _ in range(20): ripl.observe("(f)", "true")

  predictions = collectSamples(ripl,3)
  ans = [(False,.25), (True,.75)]
  return reportKnownDiscrete("TestMakeBetaBernoulli1 (%s)" % maker, ans, predictions)

def testMakeBetaBernoulli2():
  for maker in ["make_beta_bernoulli","make_uc_beta_bernoulli"]:
    yield checkMakeBetaBernoulli2,maker

# These three represent mechanisable ways of fuzzing a program for
# testing language feature interactions (in this case AAA with
# constraint forwarding and brush).
@statisticalTest
def checkMakeBetaBernoulli2(maker):
  ripl = config["get_ripl"]()

  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "((lambda () (%s ((lambda () a)) ((lambda () a)))))" % maker)
  ripl.predict("(f)")

  for _ in range(20): ripl.observe("((lambda () (f)))", "true")

  predictions = collectSamples(ripl,3)
  ans = [(False,.25), (True,.75)]
  return reportKnownDiscrete("TestMakeBetaBernoulli2 (%s)" % maker, ans, predictions)

def testMakeBetaBernoulli3():
  for maker in ["make_beta_bernoulli","make_uc_beta_bernoulli"]:
    yield checkMakeBetaBernoulli3,maker

@statisticalTest
def checkMakeBetaBernoulli3(maker):
  ripl = config["get_ripl"]()

  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "(%s a a)" % maker)
  ripl.predict("(f)")

  for _ in range(10): ripl.observe("(f)", "true")
  for _ in range(10): ripl.observe("""
(if (lt a 10.0)
  (f)
  (f))""", "true")

  predictions = collectSamples(ripl,3)
  ans = [(False,.25), (True,.75)]
  return reportKnownDiscrete("TestMakeBetaBernoulli3 (%s)" % maker, ans, predictions)

def testMakeBetaBernoulli4():
  for maker in ["make_beta_bernoulli","make_uc_beta_bernoulli"]:
    yield checkMakeBetaBernoulli4,maker

@statisticalTest
def checkMakeBetaBernoulli4(maker):
  ripl = config["get_ripl"]()

  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", """
(if (lt a 10.0)
  ({0} a a)
  ({0} a a))""".format(maker))
  ripl.predict("(f)")

  for _ in range(20): ripl.observe("(f)", "true")

  predictions = collectSamples(ripl,3)
  ans = [(False,.25), (True,.75)]
  return reportKnownDiscrete("TestMakeBetaBernoulli4 (%s)" % maker, ans, predictions)


##### (3) Staleness

# TODO write better ones, and include arrays.
# This section should not hope to find staleness, since all backends should
# assert that a makerNode has been regenerated before applying it.
# Therefore this section should try to trigger that assertion.

@statisticalTest
def testStaleAAA1():
  ripl = config["get_ripl"]()

  ripl.assume("a", "1.0")
  ripl.assume("f", "(make_uc_sym_dir_mult a 2)")
  ripl.assume("g", "(mem f)")
  ripl.assume("h", "g")
  ripl.predict("(h)")

  for _ in range(9):
    ripl.observe("(f)", "atom<1>")

  predictions = collectSamples(ripl,5,infer="mixes_slowly")
  ans = [(1,.9), (0,.1)]
  return reportKnownDiscrete("TestStaleAAA1", ans, predictions)

@statisticalTest
def testStaleAAA2():
  ripl = config["get_ripl"]()

  ripl.assume("a", "1.0")
  ripl.assume("f", "(make_uc_sym_dir_mult a 2)")
  ripl.assume("g", "(lambda () f)")
  ripl.assume("h", "(g)")
  ripl.predict("(h)")

  for _ in range(9):
    ripl.observe("(f)", "atom<1>")

  predictions = collectSamples(ripl,5,infer="mixes_slowly")
  ans = [(1,.9), (0,.1)]
  return reportKnownDiscrete("TestStaleAAA2", ans, predictions)
