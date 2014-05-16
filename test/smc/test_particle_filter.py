import math
import scipy.stats as stats
from nose import SkipTest
from testconfig import config
from venture.test.stats import statisticalTest, reportKnownContinuous, reportKnownDiscrete
from venture.test.config import get_ripl, collectSamples, defaultKernel


def testIncorporateDoesNotCrash():
  """A sanity test for stack handling of incorporate"""
  if config["get_ripl"] != "lite": raise SkipTest("Clone only implemented in lite")
  ripl = get_ripl()
  P = 60
  ripl.assume("f","""
(mem (lambda (i)
  (if (eq i 0)
    (bernoulli 0.5)
    (if (f (- i 1))
      (bernoulli 0.7)
      (bernoulli 0.3)))))
""")

  ripl.assume("g","""
(mem (lambda (i)
  (if (f i)
    (bernoulli 0.8)
    (bernoulli 0.1))))
""")

  ripl.infer("(resample %d)" % P)
  ripl.observe("(g 1)",False)
  ripl.infer("(incorporate)") # not necessary, just testing that it doesn't crash


@statisticalTest
def testBasicParticleFilter():
  """A sanity test for particle filtering"""
  if config["get_ripl"] != "lite": raise SkipTest("Clone only implemented in lite")
  ripl = get_ripl()
  P = 60
  ripl.assume("f","""
(mem (lambda (i)
  (if (eq i 0)
    (bernoulli 0.5)
    (if (f (- i 1))
      (bernoulli 0.7)
      (bernoulli 0.3)))))
""")

  ripl.assume("g","""
(mem (lambda (i)
  (if (f i)
    (bernoulli 0.8)
    (bernoulli 0.1))))
""")

  ripl.infer("(resample %d)" % P)
  ripl.observe("(g 1)",False)
  ripl.infer("(resample %d)" % P)
  ripl.observe("(g 2)",False)
  ripl.infer("(resample %d)" % P)
  ripl.observe("(g 3)",True)
  ripl.infer("(resample %d)" % P)
  ripl.observe("(g 4)",False)
  ripl.infer("(resample %d)" % P)
  ripl.observe("(g 5)",False)
  ripl.infer("(resample 1)")
  ripl.predict("(g 6)")
  
  predictions = [trace.extractValue(8)['value'] for trace in ripl.sivm.core_sivm.engine.traces]
  ans = [(0,0.6528), (1,0.3472)]
  return reportKnownDiscrete(ans, predictions)
