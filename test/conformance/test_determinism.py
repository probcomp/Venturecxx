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

"""Test that fixing Venture's initial seed makes it deterministic.

Also independent of the global randomness.

"""

import numbers
import numpy as np

from nose.tools import eq_

import venture.value.dicts as vd

from venture.lite.sp_registry import builtInSPs
from venture.test.config import broken_in
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
  r1 = get_ripl(seed=1)
  ans = r1.evaluate(prog)
  assert isinstance(ans, tp)
  for _ in range(trials):
    eq_(ans, get_ripl(seed=1).evaluate(prog))
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
  def doit(seed):
    r = get_ripl(seed=seed)
    r.bind_foreign_sp("my_normal", lite_normal_sp)
    r.assume("x", "(my_normal 0 1)")
    r.infer("(default_markov_chain 3)")
    return r.sample("x")
  ans = doit(1)
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
  ans = get_ripl(seed=1).evaluate(prog1)
  eq_(ans, get_ripl(seed=1).evaluate(prog2))
  eq_(ans, get_ripl(seed=1).evaluate(prog3))

@on_inf_prim("none")
def testFuturesDiverge1():
  r = get_ripl(seed=1)
  [x1, x2, x3] = r.evaluate("""
(do (resample 3)
    (sample_all (normal 0 1)))""")
  assert x1 != x2
  assert x1 != x3
  assert x2 != x3

@on_inf_prim("none")
@broken_in("puma", "Puma does not support enumerative diversify")
def testFuturesDiverge2():
  r = get_ripl(seed=1)
  [x1, x2, x3, x4] = r.evaluate("""
(do (assume frob (flip))
    (assume nozzle (flip))
    (enumerative_diversify default all)
    (sample_all (normal 0 1)))""")
  assert x1 != x2
  assert x1 != x3
  assert x1 != x4
  assert x2 != x3
  assert x2 != x4
  assert x3 != x4

@on_inf_prim("none")
@broken_in("puma", "Puma is nondeterministic")
def test_sample_determinism():
  r = pablo(3)
  s = pablo(3)
  assert np.array_equal(
    r.sample_all("get_datapoint(11)"), s.sample_all("get_datapoint(11)"))

@on_inf_prim("none")
@broken_in("puma", "Puma is nondeterministic")
def test_ll_determinism1():
  r = pablo(3)
  assert np.array_equal(
    r.infer("global_log_likelihood"), r.infer("global_log_likelihood"))

@on_inf_prim("none")
@broken_in("puma", "Puma is nondeterministic")
def test_lj_determinism1():
  r = pablo(3)
  assert np.array_equal(
    r.infer("global_log_joint"), r.infer("global_log_joint"))

@on_inf_prim("none")
@broken_in("puma", "Puma is nondeterministic")
def test_ll_determinism2():
  r = pablo(3)
  s = pablo(3)
  assert np.array_equal(
    r.infer("global_log_likelihood"), s.infer("global_log_likelihood"))

@on_inf_prim("none")
@broken_in("puma", "Puma is nondeterministic")
def test_lj_determinism2():
  r = pablo(3)
  s = pablo(3)
  assert np.array_equal(
    r.infer("global_log_joint"), s.infer("global_log_joint"))

@on_inf_prim("none")
@broken_in("puma", "Puma is nondeterministic")
def test_ll_effects():
  r = pablo(3)
  s = pablo(3)
  r.infer("global_log_likelihood")
  assert np.array_equal(
    r.sample_all("get_datapoint(11)"), s.sample_all("get_datapoint(11)"))

@on_inf_prim("none")
@broken_in("puma", "Puma is nondeterministic")
def test_lj_effects():
  r = pablo(3)
  s = pablo(3)
  r.infer("global_log_joint")
  assert np.array_equal(
    r.sample_all("get_datapoint(11)"), s.sample_all("get_datapoint(11)"))

@on_inf_prim("none")
@broken_in("puma", "Puma is nondeterministic")
def test_infer_sample_determinism():
  r = pablo(3)
  s = pablo(3)
  r.infer('default_markov_chain(10)')
  s.infer('default_markov_chain(10)')
  assert np.array_equal(
    r.sample_all("get_datapoint(11)"), s.sample_all("get_datapoint(11)"))

@on_inf_prim("none")
@broken_in("puma", "Puma is nondeterministic")
def test_infer_ll_determinism1():
  r = pablo(3)
  r.infer('default_markov_chain(10)')
  assert np.array_equal(
    r.infer("global_log_likelihood"), r.infer("global_log_likelihood"))

@on_inf_prim("none")
@broken_in("puma", "Puma is nondeterministic")
def test_infer_lj_determinism1():
  r = pablo(3)
  r.infer('default_markov_chain(10)')
  assert np.array_equal(
    r.infer("global_log_joint"), r.infer("global_log_joint"))

@on_inf_prim("none")
@broken_in("puma", "Puma is nondeterministic")
def test_infer_ll_determinism2():
  r = pablo(3)
  s = pablo(3)
  r.infer('default_markov_chain(10)')
  s.infer('default_markov_chain(10)')
  assert np.array_equal(
    r.infer("global_log_likelihood"), s.infer("global_log_likelihood"))

@on_inf_prim("none")
@broken_in("puma", "Puma is nondeterministic")
def test_infer_lj_determinism2():
  r = pablo(3)
  s = pablo(3)
  r.infer('default_markov_chain(10)')
  s.infer('default_markov_chain(10)')
  assert np.array_equal(
    r.infer("global_log_joint"), s.infer("global_log_joint"))

@on_inf_prim("none")
@broken_in("puma", "Puma is nondeterministic")
def test_infer_ll_effects():
  r = pablo(3)
  s = pablo(3)
  r.infer('default_markov_chain(10)')
  s.infer('default_markov_chain(10)')
  r.infer("global_log_likelihood")
  assert np.array_equal(
    r.sample_all("get_datapoint(11)"), s.sample_all("get_datapoint(11)"))

@on_inf_prim("none")
@broken_in("puma", "Puma is nondeterministic")
def test_infer_lj_effects():
  r = pablo(3)
  s = pablo(3)
  r.infer('default_markov_chain(10)')
  s.infer('default_markov_chain(10)')
  r.infer("global_log_joint")
  assert np.array_equal(
    r.sample_all("get_datapoint(11)"), s.sample_all("get_datapoint(11)"))

def pablo(nparticles):
  # Example program from Github issue #571.
  r = get_ripl(seed=1)
  r.set_mode("venture_script")
  r.execute_program("""
    // Collapsed Dirichlet Process Mixture model using
    // a Chinese Restaurant Process

    // CRP and cluster
    assume crp = make_crp(10);
    assume get_cluster = mem(proc(id){
      tag(quote(clustering), id, crp())
    });

    // Components
    assume cmvn =  mem(proc(cluster){
      make_niw_normal(array(1, 1),1,2 + 1,matrix(array(array(1,0),array(0,1))))
    });

    // Sample data
    assume get_datapoint = mem(proc(id){
      cmvn(get_cluster(id))()
    });
  """)
  r.observe("get_datapoint(1)",vd.list([vd.real(12.4299342152),vd.real(11.0243723622)]))
  r.observe("get_datapoint(2)",vd.list([vd.real(0.0876588636563),vd.real(0.46296506961)]))
  r.observe("get_datapoint(3)",vd.list([vd.real(-7.99964564506),vd.real(-8.98731353208)]))
  r.observe("get_datapoint(4)",vd.list([vd.real(8.23541122165),vd.real(7.79102768844)]))
  r.observe("get_datapoint(5)",vd.list([vd.real(0.974810779937),vd.real(1.38726814618)]))
  r.observe("get_datapoint(6)",vd.list([vd.real(9.01950900535),vd.real(9.30739440906)]))
  r.observe("get_datapoint(7)",vd.list([vd.real(-10.5666520344),vd.real(-9.79815099761)]))
  r.observe("get_datapoint(8)",vd.list([vd.real(-0.298512623055),vd.real(-0.893928070534)]))
  r.observe("get_datapoint(9)",vd.list([vd.real(12.0800451026),vd.real(7.67721242372)]))
  r.observe("get_datapoint(10)",vd.list([vd.real(8.77103714879),vd.real(9.60268348563)]))
  r.infer("resample(%d)" % (nparticles,))
  return r
