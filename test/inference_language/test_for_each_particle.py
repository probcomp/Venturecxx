# Copyright (c) 2015 MIT Probabilistic Computing Project.
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

from nose.tools import assert_raises
from nose.tools import eq_

from venture.test.config import broken_in
from venture.test.config import default_num_samples
from venture.test.config import default_num_transitions_per_sample
from venture.test.config import gen_on_inf_prim
from venture.test.config import get_ripl
from venture.test.config import on_inf_prim
from venture.test.stats import reportKnownGaussian
from venture.test.stats import reportPassage
from venture.test.stats import statisticalTest

@on_inf_prim("for_each_particle")
def testForEachParticleSmoke():
  ripl = get_ripl()
  eq_([5], ripl.infer("(for_each_particle (return 5))"))
  eq_(5, ripl.infer("(on_particle 0 (return 5))"))

@gen_on_inf_prim("for_each_particle")
def testForEachParticleSmoke2():
  for mode in ["", "_serializing", "_threaded", "_thread_ser", "_multiprocess"]:
    yield checkForEachParticleSmoke2, mode

def checkForEachParticleSmoke2(mode):
  n = max(2, default_num_samples())
  ripl = get_ripl()
  ripl.infer("(resample%s %s)" % (mode, n))
  eq_([5 for _ in range(n)], ripl.infer("(for_each_particle (return 5))"))
  eq_(5, ripl.infer("(on_particle 1 (return 5))"))

@gen_on_inf_prim("for_each_particle")
def testForEachParticleIsIndependent():
  for mode in ["", "_serializing", "_threaded", "_thread_ser", "_multiprocess"]:
    for prop in [propNotAllEqual, propDistributedNormally]:
      yield checkForEachParticleIsIndependent, mode, prop

@statisticalTest
def checkForEachParticleIsIndependent(mode, prop, seed):
  n = max(2, default_num_samples())
  ripl = get_ripl(seed=seed)
  ripl.infer("(resample%s %s)" % (mode, n))
  predictions = ripl.infer("(for_each_particle (sample (normal 0 1)))")
  return prop(predictions)

def propNotAllEqual(predictions):
  assert len(set(predictions)) > 1
  return reportPassage()

def propDistributedNormally(predictions):
  return reportKnownGaussian(0, 1, predictions)

@gen_on_inf_prim("for_each_particle")
def testForEachParticleCustomMH():
  for mode in ["", "_serializing", "_threaded", "_thread_ser", "_multiprocess"]:
    yield checkForEachParticleCustomMH, mode

@broken_in("puma", "Does not support the regen SP yet")
@statisticalTest
def checkForEachParticleCustomMH(mode, seed):
  n = max(2, default_num_samples())
  ripl = get_ripl(seed=seed, persistent_inference_trace=True)
  ripl.define("drift_mh", """\
(lambda (scope block)
  (mh_correct
   (on_subproblem default all
     (symmetric_local_proposal
      (lambda (x) (normal x 1))))))
""")
  ripl.assume("x", "(normal 0 1)")
  ripl.observe("(normal x 1)", 2)
  ripl.infer("(resample%s %s)" % (mode, n))
  for _ in range(default_num_transitions_per_sample()):
    ripl.infer("(for_each_particle (drift_mh default all))")
  predictions = ripl.infer("(for_each_particle (sample x))")
  return reportKnownGaussian(1, 0.5**0.5, predictions)

@on_inf_prim("for_each_particle")
def testForEachParticleNoModeling():
  ripl = get_ripl()
  with assert_raises(Exception):
    ripl.infer("(for_each_particle (assume x (normal 0 1)))")
  ripl.assume("x", 0)
  eq_(0, ripl.sample("x"))

@on_inf_prim("on_particle")
def testHitsOneParticle():
  ripl = get_ripl()
  ripl.execute_program("""
(do (resample 2)
    (assume x (normal 0 1))
    (on_particle 0 (force x 0))
    (on_particle 1 (force x 1)))""")
  eq_([0, 1], ripl.sample_all("x"))
