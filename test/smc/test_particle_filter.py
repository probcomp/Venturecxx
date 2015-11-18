# Copyright (c) 2013, 2014, 2015 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

import math
from venture.test.stats import statisticalTest, reportKnownDiscrete
from venture.test.stats import reportKnownGaussian
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

@on_inf_prim("resample")
@statisticalTest
def testResampling1(P=10):
  ripl = get_ripl()
  def a_sample():
    ripl.clear()
    ripl.infer("(resample %d)" % P)
    ripl.assume("x", "(normal 0 1)")
    ripl.observe("(normal x 1)", 2)
    ripl.infer("(resample 1)")
    return ripl.sample("x")
  predictions = [a_sample() for _ in range(default_num_samples())]
  return reportKnownGaussian(1, math.sqrt(0.5), predictions)

@on_inf_prim("resample")
@statisticalTest
@attr("slow")
def testResampling2(P=20):
  "This differs from testResampling1 by an extra resample step, which is supposed to be harmless"
  ripl = get_ripl()
  def a_sample():
    ripl.clear()
    ripl.infer("(resample %d)" % P)
    ripl.assume("x", "(normal 0 1)")
    ripl.observe("(normal x 1)", 2)
    ripl.infer("(incorporate)")
    ripl.infer("(resample %d)" % P)
    ripl.infer("(incorporate)")
    ripl.infer("(resample 1)")
    return ripl.sample("x")
  predictions = [a_sample() for _ in range(4*default_num_samples())]
  return reportKnownGaussian(1, math.sqrt(0.5), predictions)

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

  return reportKnownGaussian(390/89.0, math.sqrt(55/89.0), predictions)
