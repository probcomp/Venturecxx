from venture.shortcuts import *
from stat_helpers import *
from test_globals import N, globalKernel

def RIPL(): return make_lite_church_prime_ripl()

# TODO this is just one idea for how to encode matrices. 
# Not sure what the interface to make_lazy_hmm should be.
# Note that different backends have used different conventions
# for row/column vectors, so I want to make that explicit.
def testHMMSP1(N):
  ripl = RIPL()
  ripl.assume("f","""
(make_lazy_hmm
 (matrix 2 1 
         0.5 
         0.5)
 (matrix 2 2 
         0.7 0.3
         0.3 0.7)
 (matrix 2 2
         0.9 0.2
         0.1 0.8))
""");
  ripl.observe("(f 1)","atom<0>")
  ripl.observe("(f 2)","atom<0>")
  ripl.observe("(f 3)","atom<1>")
  ripl.observe("(f 4)","atom<0>")
  ripl.observe("(f 5)","atom<0>")
  ripl.predict("(f 6)")
  ripl.predict("(f 7)")
  ripl.predict("(f 8)")

  predictions = collectSamples(ripl,7,N)
  ans = [(0,0.6528), (1,0.3472)]
  return reportKnownDiscrete("testHMMSP1", ans, predictions)
