from venture.test.stats import *
from testconfig import config

# TODO this is just one idea for how to encode matrices. 
# Not sure what the interface to make_lazy_hmm should be.
# Note that different backends have used different conventions
# for row/column vectors, so I want to make that explicit.
@statisticalTest
def testHMMSP1():
  ripl = config["get_ripl"]()
  ripl.assume("f","""
(make_lazy_hmm
 (matrix (list 0.5 0.5))
 (matrix (list (list 0.7 0.3)
               (list 0.3 0.7)))
 (matrix (list (list 0.9 0.2)
               (list 0.1 0.8))))
""");
  ripl.observe("(f 1)","atom<0>")
  ripl.observe("(f 2)","atom<0>")
  ripl.observe("(f 3)","atom<1>")
  ripl.observe("(f 4)","atom<0>")
  ripl.observe("(f 5)","atom<0>")
  ripl.predict("(f 6)",label="pid")
  ripl.predict("(f 7)")
  ripl.predict("(f 8)")

  predictions = collectSamples(ripl,"pid")
  ans = [(0,0.6528), (1,0.3472)]
  return reportKnownDiscrete("testHMMSP1", ans, predictions)

@statisticalTest
def testHMMSP2():
  ripl = config["get_ripl"]()
  ripl.assume("f","""
(if (flip)
(make_lazy_hmm
 (matrix (list 0.5 0.5))
 (matrix (list (list 0.7 0.3)
               (list 0.3 0.7)))
 (matrix (list (list 0.9 0.2)
               (list 0.1 0.8))))
(make_lazy_hmm
 (matrix (list 0.5 0.5))
 (matrix (list (list 0.7 0.3)
               (list 0.3 0.7)))
 (matrix (list (list 0.9 0.2)
               (list 0.1 0.8)))))
""");
  ripl.observe("(f 1)","atom<0>")
  ripl.observe("(f 2)","atom<0>")
  ripl.observe("(f 3)","atom<1>")
  ripl.observe("(f 4)","atom<0>")
  ripl.observe("(f 5)","atom<0>")
  ripl.predict("(f 6)",label="pid")
  ripl.predict("(f 7)")
  ripl.predict("(f 8)")

  predictions = collectSamples(ripl,"pid")
  ans = [(0,0.6528), (1,0.3472)]
  return reportKnownDiscrete("testHMMSP2", ans, predictions)
