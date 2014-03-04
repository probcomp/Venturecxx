from venture.test.config import get_ripl, collectSamples, defaultKernel
from nose.tools import eq_

def testForgetContinuousInference():
  ripl = get_ripl()
  ripl.predict("(flip)")
  ripl.predict("(flip)")
  ripl.infer(10)
  ripl.forget(1)
  ripl.forget(2)
  ripl.predict("(flip)")
  ripl.infer(10)
