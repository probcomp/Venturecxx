from venture.shortcuts import *
from stat_helpers import *
from test_globals import N, globalKernel

def RIPL(): return make_lite_church_prime_ripl()

def testOuterMix1(N):
  "Makes sure that the mix-mh weights are correct"
  ripl = RIPL()
  ripl.predict("(if (bernoulli 0.5) (if (bernoulli 0.5) 2 3) 1)")

  predictions = collectSamples(ripl,1,N)
  ans = [(1,.5), (2,.25), (3,.25)]
  return reportKnownDiscrete("TestOuterMix1", ans, predictions)

