import scipy.stats as stats
from venture.test.stats import statisticalTest, reportKnownContinuous, reportKnownDiscrete
from nose import SkipTest
from venture.test.config import get_ripl, collectSamples, collect_iid_samples

@statisticalTest
def testBlockingExample0():
  ripl = get_ripl()
  if not collect_iid_samples(): raise SkipTest("This test should not pass without reset.")
  
  ripl.assume("a", "(scope_include 0 0 (normal 10.0 1.0))")
  ripl.assume("b", "(scope_include 1 1 (normal a 1.0))")
  ripl.observe("(normal b 1.0)", 14.0)

  # If inference only frobnicates b, then the distribution on a
  # remains the prior.
  predictions = collectSamples(ripl,1,infer={"transitions":10,"kernel":"mh","scope":1,"block":1})
  cdf = stats.norm(loc=10.0, scale=1.0).cdf
  return reportKnownContinuous(cdf, predictions, "N(10.0,1.0)")

def testBlockingExample1():
  ripl = get_ripl()
  ripl.assume("a", "(scope_include 0 0 (normal 0.0 1.0))")
  ripl.assume("b", "(scope_include 0 0 (normal 1.0 1.0))")
  olda = ripl.report(1)
  oldb = ripl.report(2)
  # The point of block proposals is that both things change at once.
  ripl.sivm.core_sivm.engine.infer({"transitions":1, "kernel":"mh", "scope":0, "block":0})
  newa = ripl.report(1)
  newb = ripl.report(2)
  assert not olda == newa
  assert not oldb == newb

def testBlockingExample2():
  ripl = get_ripl()
  ripl.assume("a", "(scope_include 0 0 (normal 0.0 1.0))")
  ripl.assume("b", "(scope_include 0 0 (normal 1.0 1.0))")
  ripl.assume("c", "(scope_include 0 1 (normal 2.0 1.0))")
  ripl.assume("d", "(scope_include 0 1 (normal 3.0 1.0))")
  olda = ripl.report(1)
  oldb = ripl.report(2)
  oldc = ripl.report(3)
  oldd = ripl.report(4)
  # Should change everything in one or the other block
  ripl.sivm.core_sivm.engine.infer({"transitions":1, "kernel":"mh", "scope":0, "block":"one"})
  newa = ripl.report(1)
  newb = ripl.report(2)
  newc = ripl.report(3)
  newd = ripl.report(4)
  if olda == newa:
    assert oldb == newb
    assert not oldc == newc
    assert not oldd == newd
  else:
    assert not oldb == newb
    assert oldc == newc
    assert oldd == newd

def testBlockingExample3():
  ripl = get_ripl()
  ripl.assume("a", "(scope_include 0 0 (normal 0.0 1.0))")
  ripl.assume("b", "(scope_include 0 1 (normal 1.0 1.0))")
  olda = ripl.report(1)
  oldb = ripl.report(2)
  # The point of block proposals is that both things change at once.
  ripl.sivm.core_sivm.engine.infer({"transitions":1, "kernel":"mh", "scope":0, "block":"all"})
  newa = ripl.report(1)
  newb = ripl.report(2)
  assert not olda == newa
  assert not oldb == newb

@statisticalTest
def testBasicRejection1():
  ripl = get_ripl()
  ripl.assume("x", "(bernoulli 0.5)")
  predictions = collectSamples(ripl, 1, infer={"kernel":"reject", "scope":"default", "block":"all", "transitions":1})
  ans = [(True, 0.5), (False, 0.5)]
  return reportKnownDiscrete(ans, predictions)

@statisticalTest
def testBasicRejection2():
  ripl = get_ripl()
  ripl.assume("p", "(uniform_continuous 0 1)")
  ripl.assume("x", "(bernoulli p)")
  predictions = collectSamples(ripl, 2, infer={"kernel":"reject", "scope":"default", "block":"all", "transitions":1})
  ans = [(True, 0.5), (False, 0.5)]
  return reportKnownDiscrete(ans, predictions)
