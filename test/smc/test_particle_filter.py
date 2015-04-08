import math
import scipy.stats as stats
from venture.test.stats import statisticalTest, reportKnownContinuous, reportKnownDiscrete
from venture.test.config import get_ripl, default_num_samples, on_inf_prim
import sys
from nose.plugins.attrib import attr

sys.setrecursionlimit(10000)

@on_inf_prim("resample")
def testIncorporateDoesNotCrash():
  """A sanity test for stack handling of incorporate"""

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
  ripl.infer("(incorporate)")

def initBasicPFripl1():
  ripl = get_ripl()
  ripl.assume("f","""
(mem (lambda (i)
  (tag 0 i 
    (bernoulli (if (eq i 0) 0.5 
                   (if (f (- i 1)) 0.7 0.3))))))
""")

  ripl.assume("g","""
(mem (lambda (i)
  (bernoulli (if (f i) 0.8 0.1))))
""")

  return ripl

@on_inf_prim("all") # Really resample and mh
@statisticalTest
@attr("slow")
def testBasicParticleFilter1(P = 10):
  """A sanity test for particle filtering (discrete)"""

  N = default_num_samples()
  predictions = []

  os = zip(range(1,6),[False,False,True,False,False])

  for _ in range(N):
    ripl = initBasicPFripl1()
    for t,val in os:
      ripl.infer("(resample %d)" % P)
      ripl.predict("(f %d)" % t)
      ripl.infer("(mh 0 %d 5)" % t)
      ripl.observe("(g %d)" % t,val)

    ripl.infer("(resample 1)")
    ripl.predict("(g 6)",label="pid")
    predictions.append(ripl.report("pid"))

  ans = [(0,0.6528), (1,0.3472)]
  return reportKnownDiscrete(ans, predictions)

##################

def initBasicPFripl2():
  ripl = get_ripl()
  ripl.assume("f","""
(mem (lambda (i)
  (tag 0 i 
    (normal (if (eq i 0) 0 (f (- i 1))) 1))))
""")

  ripl.assume("g","""
(mem (lambda (i)
  (normal (f i) 1.0)))
""")

  return ripl

@on_inf_prim("all") # Really resample and mh
@statisticalTest
@attr("slow")
def testBasicParticleFilter2(P = 10):
  """A sanity test for particle filtering (continuous)"""

  N = default_num_samples()
  predictions = []

  os = zip(range(0,5),[1,2,3,4,5])

  for _ in range(N):
    ripl = initBasicPFripl2()
    for t,val in os:
      ripl.infer("(resample %d)" % P)
      ripl.predict("(f %d)" % t)
      ripl.infer("(mh 0 %d 5)" % t)
      ripl.observe("(g %d)" % t,val)

    ripl.infer("(resample 1)")
    ripl.predict("(f 4)",label="pid")
    predictions.append(ripl.report("pid"))

  cdf = stats.norm(loc=390/89.0, scale=math.sqrt(55/89.0)).cdf
  return reportKnownContinuous(cdf, predictions, "N(4.382, 0.786)")
