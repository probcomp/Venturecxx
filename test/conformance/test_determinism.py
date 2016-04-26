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

"""Test that fixing Venture's initial entropy makes it deterministic.

Also independent of the global randomness.

"""

import numbers

from nose.tools import eq_

from venture.lite.sp_registry import builtInSPs
from venture.test.config import gen_on_inf_prim
from venture.test.config import get_ripl
from venture.test.config import on_inf_prim

@gen_on_inf_prim("none") # Doesn't exercise any statistical properties
def testDeterminismSmoke():
  def on_one_cont_var(infer):
    return """(do (assume x (normal 0 1)) %s (sample x))""" % (infer,)
  def on_one_disc_var(infer):
    return """(do (assume x (flip)) %s (sample x))""" % (infer,)

  for prog in ["(normal 0 1)",
               "(sample (normal 0 1))"]:
    yield checkDeterminismSmoke, prog, True

  for prog in [on_one_cont_var("(mh default one 1)"),
               on_one_cont_var("(func_mh default one 1)"),
               on_one_cont_var("(slice default one 0.2 10 1)"),
               on_one_cont_var("(slice_doubling default one 0.2 10 1)"),
               on_one_cont_var("(func_pgibbs default ordered 3 2)"),
               on_one_cont_var("(meanfield default one 5 2)"),
               on_one_cont_var("(hmc default one 0.2 5 2)"),
               on_one_cont_var("(rejection default one)"),
               on_one_cont_var("(bogo_possibilize default one 1)"),
               ]:
    yield checkDeterminismSmoke, prog

  two_var_mh = """(do
    (assume x (normal 0 1))
    (assume y (normal 0 1))
    (mh default one 5)
    (sample x))"""
  for prog in [on_one_disc_var("(mh default one 1)"),
               on_one_disc_var("(gibbs default one 1)"),
               on_one_disc_var("(func_pgibbs default ordered 3 2)"),
               on_one_disc_var("(rejection default one)"),
               on_one_disc_var("(bogo_possibilize default one 1)"),
               two_var_mh,
               ]:
    yield checkDeterminismSmoke, prog, False, 5

  for prog in ["(do (resample 3) (sample_all (normal 0 1)))",
               "(do (resample_serializing 3) (sample_all (normal 0 1)))",
               "(do (resample_threaded 3) (sample_all (normal 0 1)))",
               "(do (resample_thread_ser 3) (sample_all (normal 0 1)))",
               "(do (resample_multiprocess 3) (sample_all (normal 0 1)))",
               "(do (resample_multiprocess 3 2) (sample_all (normal 0 1)))",
               ]:
    yield checkDeterminismSmoke, prog, False, 1, list

def checkDeterminismSmoke(prog, repeatable=False, trials=1, tp=numbers.Number):
  r1 = get_ripl(entropy=1)
  ans = r1.evaluate(prog)
  print ans
  assert isinstance(ans, tp)
  for _ in range(trials):
    eq_(ans, get_ripl(entropy=1).evaluate(prog))
  if repeatable:
    assert ans != r1.evaluate(prog)

@gen_on_inf_prim("none") # Doesn't exercise any statistical properties
def testForEachParticleDeterminism():
  for_each_particle_prog1 = """
(do (resample 10)
    (for_each_particle
     (action (flip))))"""
  yield checkDeterminismSmoke, for_each_particle_prog1, False, 1, list

  for_each_particle_prog2 = """
(do (resample 10)
    (assume x (normal 0 1))
    (for_each_particle
     (do pass (if (flip) (mh default one 1) pass)))
    (sample_all x))"""
  yield checkDeterminismSmoke, for_each_particle_prog2, False, 1, list

@on_inf_prim("none") # Doesn't exercise any statistical properties
def testModelSwapDeterminism():
  prog = """
(do (resample 5)
    (assume x (normal 0 1))
    (m <- (new_model))
    (p <- (in_model m
     (do (resample 5)
         (assume x (normal 0 1))
         (sample_all x))))
    (return (first p)))"""
  checkDeterminismSmoke(prog, tp=list)

@on_inf_prim("none") # Doesn't exercise any statistical properties
def testModelForkDeterminism1():
  prog = """
(do (resample 5)
    (assume x (normal 0 1))
    (m <- (fork_model))
    (p <- (in_model m (sample_all x)))
    (return (first p)))"""
  checkDeterminismSmoke(prog, tp=list)

@on_inf_prim("none") # Doesn't exercise any statistical properties
def testModelForkDeterminism2():
  prog = """
(do (resample 5)
    (assume x (normal 0 1))
    (m <- (fork_model))
    (p <- (in_model m
     (do (assume y (normal 0 1))
         (sample_all y))))
    (return (first p)))"""
  checkDeterminismSmoke(prog, tp=list)

@on_inf_prim("none") # Doesn't exercise any statistical properties
def testForeignDeterminismSmoke():
  get_ripl() # Build the SP registry (TODO !?)
  lite_normal_sp = builtInSPs()["normal"]
  def doit(entropy):
    r = get_ripl(entropy=entropy)
    r.bind_foreign_sp("my_normal", lite_normal_sp)
    r.assume("x", "(my_normal 0 1)")
    r.infer("(default_markov_chain 3)")
    return r.sample("x")
  ans = doit(1)
  print ans
  assert isinstance(ans, numbers.Number)
  eq_(ans, doit(1))
  assert ans != doit(2)

@on_inf_prim("none")
def testDeterministicUnderChunking():
  prog1 = """
(do (resample 3)
    (sample_all (normal 0 1)))"""
  prog2 = """
(do (resample_multiprocess 3)
    (sample_all (normal 0 1)))"""
  prog3 = """
(do (resample_multiprocess 3 2)
    (sample_all (normal 0 1)))"""
  ans = get_ripl(entropy=1).evaluate(prog1)
  eq_(ans, get_ripl(entropy=1).evaluate(prog2))
  eq_(ans, get_ripl(entropy=1).evaluate(prog3))
