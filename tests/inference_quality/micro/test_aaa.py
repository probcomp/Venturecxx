from venture.shortcuts import *
from stat_helpers import *
from test_globals import N, globalKernel

def RIPL(): return make_lite_church_prime_ripl()

def testMakeSymDirMult1(name):
  ripl = RIPL()
  ripl.assume("f", "(%s 1.0 2)" % name)
  ripl.predict("(f)")
  predictions = collectSamples(ripl,2,N)
  ans = [(0,.5), (1,.5)]
  return reportKnownDiscrete("TestMakeSymDirMult1(%s)" % name, ans, predictions)

def testDirichletMultinomial1(name, ripl, index):
  for i in range(1,4):
    for j in range(20):
      ripl.observe("(f)", "atom<%d>" % i)

  predictions = collectSamples(ripl,index,N)
  ans = [(0,.1), (1,.3), (2,.3), (3,.3)]
  return reportKnownDiscrete("TestDirichletMultinomial(%s)" % name, ans, predictions)

def testMakeSymDirMult2(name):
  ripl = RIPL()
  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "(%s a 4)" % name)
  ripl.predict("(f)")
  return testDirichletMultinomial1(name, ripl, 3, N)

def testMakeDirMult1():
  ripl = RIPL()
  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "(make_dir_mult a a a a)")
  ripl.predict("(f)")
  return testDirichletMultinomial1("make_dir_mult", ripl, 3, N)

def testMakeBetaBernoulli1(maker):
  ripl = RIPL()
  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "(%s a a)" % maker)
  ripl.predict("(f)")

  for j in range(20): ripl.observe("(f)", "true")

  predictions = collectSamples(ripl,3,N)
  ans = [(False,.25), (True,.75)]
  return reportKnownDiscrete("TestMakeBetaBernoulli1 (%s)" % maker, ans, predictions)

# These three represent mechanisable ways of fuzzing a program for
# testing language feature interactions (in this case AAA with
# constraint forwarding and brush).
def testMakeBetaBernoulli2(maker):
  ripl = RIPL()
  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "((lambda () (%s ((lambda () a)) ((lambda () a)))))" % maker)
  ripl.predict("(f)")

  for j in range(20): ripl.observe("((lambda () (f)))", "true")

  predictions = collectSamples(ripl,3,N)
  ans = [(False,.25), (True,.75)]
  return reportKnownDiscrete("TestMakeBetaBernoulli2 (%s)" % maker, ans, predictions)

def testMakeBetaBernoulli3(maker):
  ripl = RIPL()
  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "(%s a a)" % maker)
  ripl.predict("(f)")

  for j in range(10): ripl.observe("(f)", "true")
  for j in range(10): ripl.observe("""
(if (lt a 10.0)
  (f)
  (f))""", "true")

  predictions = collectSamples(ripl,3,N)
  ans = [(False,.25), (True,.75)]
  return reportKnownDiscrete("TestMakeBetaBernoulli3 (%s)" % maker, ans, predictions)

def testMakeBetaBernoulli4(maker):
  ripl = RIPL()
  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", """
(if (lt a 10.0)
  ({0} a a)
  ({0} a a))""".format(maker))
  ripl.predict("(f)")

  for j in range(20): ripl.observe("(f)", "true")

  predictions = collectSamples(ripl,3,N)
  ans = [(False,.25), (True,.75)]
  return reportKnownDiscrete("TestMakeBetaBernoulli4 (%s)" % maker, ans, predictions)
