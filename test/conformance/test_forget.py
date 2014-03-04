from venture.test.config import get_ripl, collectSamples, defaultKernel
from nose.tools import eq_

def testForgetContinuousInference1():
  ripl = get_ripl()
  for i in range(10):
    pid = "pid%d" % i
    print pid
    ripl.predict("(flip)",label=pid)
    ripl.forget(pid)

def testForgetContinuousInference2():
  ripl = get_ripl()
  ripl.predict("(flip)")
#  ripl.predict("(flip)")
#  ripl.infer(10)
  ripl.forget(1)
#  ripl.forget(2)
  ripl.predict("(flip)")
#  ripl.infer(10)


