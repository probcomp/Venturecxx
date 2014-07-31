import math
import scipy.stats as stats
from nose import SkipTest

from venture.test.stats import statisticalTest, reportKnownContinuous, reportKnownDiscrete
from venture.test.config import get_ripl, collectSamples, collect_iid_samples, default_num_transitions_per_sample, broken_in, on_inf_prim

@statisticalTest
def testBlockingExample0():
  ripl = get_ripl()
  if not collect_iid_samples(): raise SkipTest("This test should not pass without reset.")
  
  ripl.assume("a", "(scope_include 0 0 (normal 10.0 1.0))", label="pid")
  ripl.assume("b", "(scope_include 1 1 (normal a 1.0))")
  ripl.observe("(normal b 1.0)", 14.0)

  # If inference only frobnicates b, then the distribution on a
  # remains the prior.
  predictions = collectSamples(ripl,"pid",infer="(mh 1 1 10)")
  cdf = stats.norm(loc=10.0, scale=1.0).cdf
  return reportKnownContinuous(cdf, predictions, "N(10.0,1.0)")

def testBlockingExample1():
  ripl = get_ripl()
  ripl.assume("a", "(scope_include 0 0 (normal 0.0 1.0))",label="a")
  ripl.assume("b", "(scope_include 0 0 (normal 1.0 1.0))",label="b")
  olda = ripl.report("a")
  oldb = ripl.report("b")
  # The point of block proposals is that both things change at once.
  ripl.infer("(mh 0 0 1)")
  newa = ripl.report("a")
  newb = ripl.report("b")
  assert not olda == newa
  assert not oldb == newb

def testBlockingExample2():
  ripl = get_ripl()
  ripl.assume("a", "(scope_include 0 0 (normal 0.0 1.0))", label="a")
  ripl.assume("b", "(scope_include 0 0 (normal 1.0 1.0))", label="b")
  ripl.assume("c", "(scope_include 0 1 (normal 2.0 1.0))", label="c")
  ripl.assume("d", "(scope_include 0 1 (normal 3.0 1.0))", label="d")
  olda = ripl.report("a")
  oldb = ripl.report("b")
  oldc = ripl.report("c")
  oldd = ripl.report("d")
  # Should change everything in one or the other block
  ripl.infer("(mh 0 one 1)")
  newa = ripl.report("a")
  newb = ripl.report("b")
  newc = ripl.report("c")
  newd = ripl.report("d")
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
  ripl.assume("a", "(scope_include 0 0 (normal 0.0 1.0))", label="a")
  ripl.assume("b", "(scope_include 0 1 (normal 1.0 1.0))", label="b")
  olda = ripl.report("a")
  oldb = ripl.report("b")
  # The point of block proposals is that both things change at once.
  ripl.infer("(mh 0 all 1)")
  newa = ripl.report("a")
  newb = ripl.report("b")
  assert not olda == newa
  assert not oldb == newb

@statisticalTest
@broken_in('puma', "rejection is not implemented in Puma")
@on_inf_prim("rejection")
def testBasicRejection1():
  ripl = get_ripl()
  ripl.assume("x", "(bernoulli 0.5)",label="pid")
  predictions = collectSamples(ripl, "pid", infer="(rejection default all 1)")
  ans = [(True, 0.5), (False, 0.5)]
  return reportKnownDiscrete(ans, predictions)

@statisticalTest
@broken_in('puma', "rejection is not implemented in Puma")
@on_inf_prim("rejection")
def testBasicRejection2():
  ripl = get_ripl()
  ripl.assume("p", "(uniform_continuous 0 1)")
  ripl.assume("x", "(bernoulli p)", label="pid")
  predictions = collectSamples(ripl, "pid", infer="(rejection default all 1)")
  ans = [(True, 0.5), (False, 0.5)]
  return reportKnownDiscrete(ans, predictions)

@statisticalTest
@broken_in('puma', "rejection is not implemented in Puma")
@on_inf_prim("rejection")
def testBasicRejection3():
  ripl = get_ripl()
  ripl.assume("p", "(uniform_continuous 0 1)", label="pid")
  ripl.observe("(bernoulli p)", "true")
  predictions = collectSamples(ripl, "pid", infer="(rejection default all 1)")
  cdf = stats.beta(2,1).cdf
  return reportKnownContinuous(cdf, predictions, "beta(2,1)")

@statisticalTest
@on_inf_prim("mh") # Also cycle, but that's not a "primitive"
def testCycleKernel():
  """Same example as testBlockingExample0, but a cycle kernel that covers everything should solve it"""
  ripl = get_ripl()

  ripl.assume("a", "(scope_include 0 0 (normal 10.0 1.0))", label="pid")
  ripl.assume("b", "(scope_include 1 1 (normal a 1.0))")
  ripl.observe("(normal b 1.0)", 14.0)

  infer = "(cycle ((mh 0 0 1) (mh 1 1 1)) %s)" % default_num_transitions_per_sample()

  predictions = collectSamples(ripl,"pid",infer=infer)
  cdf = stats.norm(loc=34.0/3.0, scale=math.sqrt(2.0/3.0)).cdf
  return reportKnownContinuous(cdf, predictions, "N(34/3,sqrt(2/3))")

@statisticalTest
@on_inf_prim("mh") # Also mixture, but that's not a "primitive"
def testMixtureKernel():
  """Same example as testCycleKernel, but with a mixture kernel"""
  ripl = get_ripl()

  ripl.assume("a", "(scope_include 0 0 (normal 10.0 1.0))", label="pid")
  ripl.assume("b", "(scope_include 1 1 (normal a 1.0))")
  ripl.observe("(normal b 1.0)", 14.0)

  infer = "(mixture (0.5 (mh 0 0 1) 0.5 (mh 1 1 1)) %s)" % default_num_transitions_per_sample()

  predictions = collectSamples(ripl,"pid",infer=infer)
  cdf = stats.norm(loc=34.0/3.0, scale=math.sqrt(2.0/3.0)).cdf
  return reportKnownContinuous(cdf, predictions, "N(34/3,sqrt(2/3))")
