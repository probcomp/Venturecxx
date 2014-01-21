from venture.test.stats import *
from testconfig import config

def testBlockingExample0():
  N = config["num_samples"]
  ripl = config["get_ripl"]()

  ripl.assume("a", "(scope_include 0 0 (normal 10.0 1.0))")
  ripl.assume("b", "(scope_include 1 1 (normal a 1.0))")
  ripl.observe("(normal b 1.0)", 14.0)

  # If inference only frobnicates b, then the distribution on a
  # remains the prior.
  predictions = collectSamplesWith(ripl,1,N,{"transitions":10,"kernel":"mh","scope":1,"block":1})
  cdf = stats.norm(loc=10.0, scale=1.0).cdf
  return reportKnownContinuous("testBlockingExample0", cdf, predictions, "N(10.0,1.0)")

def testBlockingExample1():
  ripl = config["get_ripl"]()
  ripl.assume("a", "(scope_include 0 0 (normal 0.0 1.0))")
  ripl.assume("b", "(scope_include 0 0 (normal 1.0 1.0))")
  olda = ripl.report(1)
  oldb = ripl.report(2)
  # The point of block proposals is that both things change at once.
  ripl.sivm.core_sivm.engine.infer({"transitions":1, "kernel":"mh", "scope":0, "block":0})
  newa = ripl.report(1)
  newb = ripl.report(2)
  assert not(olda == newa)
  assert not(oldb == newb)
  return reportPassage("testBlockingExample1")

def testBlockingExample2():
  ripl = config["get_ripl"]()
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
  if (olda == newa):
    assert oldb == newb
    assert not(oldc == newc)
    assert not(oldd == newd)
  else:
    assert not(oldb == newb)
    assert oldc == newc
    assert oldd == newd
  return reportPassage("testBlockingExample2")

def testBlockingExample3():
  ripl = config["get_ripl"]()
  ripl.assume("a", "(scope_include 0 0 (normal 0.0 1.0))")
  ripl.assume("b", "(scope_include 0 1 (normal 1.0 1.0))")
  olda = ripl.report(1)
  oldb = ripl.report(2)
  # The point of block proposals is that both things change at once.
  ripl.sivm.core_sivm.engine.infer({"transitions":1, "kernel":"mh", "scope":0, "block":"all"})
  newa = ripl.report(1)
  newb = ripl.report(2)
  assert not(olda == newa)
  assert not(oldb == newb)
  return reportPassage("testBlockingExample3")
