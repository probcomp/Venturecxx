import math
import scipy.stats as stats
from nose import SkipTest
from venture.test.stats import statisticalTest, reportKnownContinuous, reportKnownDiscrete
from venture.test.config import get_ripl, collectSamples, defaultKernel


@statisticalTest
def testBasicParticleFilter():
"""Poorly designed and poorly written test, which nonetheless provides a semblance of a sanity test for particle filtering"""
  ripl = get_ripl()
  P = 50
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

  ripl.sivm.core_sivm.engine.infer({'instruction':'resample','particles':P})
  ripl.observe("(g 1)",False)
  ripl.sivm.core_sivm.engine.infer({'instruction':'resample','particles':P})
  ripl.observe("(g 2)",False)
  ripl.sivm.core_sivm.engine.infer({'instruction':'resample','particles':P})
  ripl.observe("(g 3)",True)
  ripl.sivm.core_sivm.engine.infer({'instruction':'resample','particles':P})
  ripl.observe("(g 4)",False)
  ripl.sivm.core_sivm.engine.infer({'instruction':'resample','particles':P})
  ripl.observe("(g 5)",False)
  ripl.sivm.core_sivm.engine.infer({'instruction':'resample','particles':P})
  ripl.predict("(g 6)")
  
  predictions = [trace.extractValue(8)['value'] for trace in ripl.sivm.core_sivm.engine.traces]
  ans = [(0,0.6528), (1,0.3472)]
  return reportKnownDiscrete(ans, predictions)
