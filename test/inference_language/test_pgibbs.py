# Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
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
from venture.test.config import get_ripl, collectSamples
from venture.test.config import ignore_inference_quality
from venture.test.config import default_num_transitions_per_sample
from venture.test.config import gen_on_inf_prim, on_inf_prim

@gen_on_inf_prim("pgibbs")
def testPGibbsBasic1():
  yield checkPGibbsBasic1, "false"
  yield checkPGibbsBasic1, "true"

@statisticalTest
def checkPGibbsBasic1(in_parallel):
  """Basic sanity test"""
  ripl = get_ripl()
  ripl.predict("(bernoulli)",label="pid")
  infer = "(pgibbs default one 2 %s %s)" % (default_num_transitions_per_sample(), in_parallel)

  predictions = collectSamples(ripl,"pid",infer=infer)
  ans = [(True,.5),(False,.5)]
  return reportKnownDiscrete(ans, predictions)

@gen_on_inf_prim("pgibbs")
def testPGibbsBasic2():
  yield checkPGibbsBasic2, "false"
  yield checkPGibbsBasic2, "true"

@statisticalTest
def checkPGibbsBasic2(in_parallel):
  """Basic sanity test"""
  ripl = get_ripl()
  ripl.assume("x","(flip 0.1)",label="pid")
  infer = "(pgibbs default one 2 %s %s)" % (default_num_transitions_per_sample(), in_parallel)
  predictions = collectSamples(ripl,"pid",infer=infer)
  ans = [(False,.9),(True,.1)]
  return reportKnownDiscrete(ans, predictions)

# Not the same test generator because I want to annotate them differently.
@gen_on_inf_prim("pgibbs")
def testPGibbsBlockingMHHMM1():
  yield checkPGibbsBlockingMHHMM1, "pgibbs"

@gen_on_inf_prim("func_pgibbs")
def testFuncPGibbsBlockingMHHMM1():
  yield checkPGibbsBlockingMHHMM1, "func_pgibbs"

@statisticalTest
def checkPGibbsBlockingMHHMM1(operator):
  """The point of this is that it should give reasonable results in very few transitions but with a large number of particles."""
  ripl = get_ripl()

  ripl.assume("x0","(tag 0 0 (normal 0.0 1.0))")
  ripl.assume("x1","(tag 0 1 (normal x0 1.0))")
  ripl.assume("x2","(tag 0 2 (normal x1 1.0))")
  ripl.assume("x3","(tag 0 3 (normal x2 1.0))")
  ripl.assume("x4","(tag 0 4 (normal x3 1.0))")

  ripl.assume("y0","(normal x0 1.0)")
  ripl.assume("y1","(normal x1 1.0)")
  ripl.assume("y2","(normal x2 1.0)")
  ripl.assume("y3","(normal x3 1.0)")
  ripl.assume("y4","(normal x4 1.0)")

  ripl.observe("y0",1.0)
  ripl.observe("y1",2.0)
  ripl.observe("y2",3.0)
  ripl.observe("y3",4.0)
  ripl.observe("y4",5.0)
  ripl.predict("x4",label="pid")

  if ignore_inference_quality():
    infer = "(%s 0 ordered 3 2)" % operator
  else:
    infer = "(%s 0 ordered 20 10)" % operator

  predictions = collectSamples(ripl,"pid",infer=infer)
  return reportKnownGaussian(390.0/89.0, math.sqrt(55/89.0), predictions)


@gen_on_inf_prim("pgibbs")
def testPGibbsDynamicScope1():
  yield checkPGibbsDynamicScope1, "pgibbs"

@gen_on_inf_prim("func_pgibbs")
def testFuncPGibbsDynamicScope1():
  yield checkPGibbsDynamicScope1, "func_pgibbs"

@statisticalTest
def checkPGibbsDynamicScope1(operator):
  ripl = get_ripl()

  ripl.assume("transition_fn", "(lambda (x) (normal x 1.0))")
  ripl.assume("observation_fn", "(lambda (y) (normal y 1.0))")

  ripl.assume("initial_state_fn", "(lambda () (normal 0.0 1.0))")
  ripl.assume("f","""
(mem (lambda (t)
  (tag 0 t (if (= t 0) (initial_state_fn) (transition_fn (f (- t 1)))))))
""")

  ripl.assume("g","(mem (lambda (t) (observation_fn (f t))))")

  ripl.observe("(g 0)",1.0)
  ripl.observe("(g 1)",2.0)
  ripl.observe("(g 2)",3.0)
  ripl.observe("(g 3)",4.0)
  ripl.observe("(g 4)",5.0)

  ripl.predict("(f 4)","pid")

  if ignore_inference_quality():
    infer = "(%s 0 ordered 3 2)" % operator
  else:
    infer = "(%s 0 ordered 20 10)" % operator

  predictions = collectSamples(ripl,"pid",infer=infer)
  return reportKnownGaussian(390/89.0, math.sqrt(55/89.0), predictions)

@on_inf_prim("pgibbs")
@statisticalTest
def testPGibbsDynamicScopeInterval():
  ripl = get_ripl()

  ripl.assume("transition_fn", "(lambda (x) (normal x 1.0))")
  ripl.assume("observation_fn", "(lambda (y) (normal y 1.0))")

  ripl.assume("initial_state_fn", "(lambda () (normal 0.0 1.0))")
  ripl.assume("f","""
(mem (lambda (t)
  (tag 0 t (if (= t 0) (initial_state_fn) (transition_fn (f (- t 1)))))))
""")

  ripl.assume("g","(mem (lambda (t) (observation_fn (f t))))")

  ripl.observe("(g 0)",1.0)
  ripl.observe("(g 1)",2.0)
  ripl.observe("(g 2)",3.0)
  ripl.observe("(g 3)",4.0)
  ripl.observe("(g 4)",5.0)

  ripl.predict("(f 4)","pid")

  P = 3 if ignore_inference_quality() else 8
  T = 2 if ignore_inference_quality() else 10

  infer = "(do (pgibbs 0 (ordered_range 0 3) %d %d) (pgibbs 0 (ordered_range 1 4) %d %d))" % (P,P,T,T)

  predictions = collectSamples(ripl,"pid",infer=infer)
  return reportKnownGaussian(390/89.0, math.sqrt(55/89.0), predictions)

@gen_on_inf_prim("func_pgibbs")
def testFunnyHMM():
  yield checkFunnyHMM, "false"
  yield checkFunnyHMM, "true"

def checkFunnyHMM(in_parallel):
  ripl = get_ripl()

  ripl.assume("hypers", "(mem (lambda (t) (tag 0 t (normal 0 1))))")
  ripl.assume("init", "0")
  ripl.assume("next", "(lambda (state delta) (+ state delta))")
  ripl.assume("get_state",
    """(mem (lambda (t)
          (if (= t 0) init
            (next (get_state (- t 1)) (hypers t)))))""")
  ripl.assume("obs", "(mem (lambda (t) (normal (get_state t) 1)))")

  for t in range(1, 5):
    ripl.observe("(obs %d)" % t, t)

  ripl.infer("(func_pgibbs 0 ordered 3 2 %s)" % in_parallel)
