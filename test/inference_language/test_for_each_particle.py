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

from nose.tools import eq_, assert_raises
from nose import SkipTest
import scipy.stats

from venture.test.config import get_ripl, default_num_samples, gen_on_inf_prim, on_inf_prim, broken_in, default_num_transitions_per_sample
from venture.test.stats import statisticalTest, reportKnownContinuous

@on_inf_prim("for_each_particle")
def testForEachParticleSmoke():
  ripl = get_ripl()
  eq_([5], ripl.infer("(for_each_particle (return 5))"))

@gen_on_inf_prim("for_each_particle")
def testForEachParticleSmoke2():
  for mode in ["", "_serializing", "_threaded", "_thread_ser", "_multiprocess"]:
    yield checkForEachParticleSmoke2, mode

def checkForEachParticleSmoke2(mode):
  n = max(2, default_num_samples())
  ripl = get_ripl()
  ripl.infer("(resample%s %s)" % (mode, n))
  eq_([5 for _ in range(n)], ripl.infer("(for_each_particle (return 5))"))

@gen_on_inf_prim("for_each_particle")
def testForEachParticleIsIndependent():
  for mode in ["", "_serializing", "_threaded", "_thread_ser", "_multiprocess"]:
    for prop in [propNotAllEqual, propDistributedNormally]:
      yield checkForEachParticleIsIndependent, mode, prop

def checkForEachParticleIsIndependent(mode, prop):
  n = max(2, default_num_samples())
  ripl = get_ripl()
  ripl.infer("(resample%s %s)" % (mode, n))
  predictions = ripl.infer("(for_each_particle (sample (normal 0 1)))")
  prop(predictions)

def propNotAllEqual(predictions):
  assert len(set(predictions)) > 1

@statisticalTest
def propDistributedNormally(predictions):
  return reportKnownContinuous(scipy.stats.norm(loc=0, scale=1).cdf, predictions, "N(0,1)")

@gen_on_inf_prim("for_each_particle")
def testForEachParticleCustomMH():
  for mode in ["", "_serializing", "_threaded", "_thread_ser", "_multiprocess"]:
    yield checkForEachParticleCustomMH, mode

@broken_in("puma", "Does not support the regen SP yet")
@statisticalTest
def checkForEachParticleCustomMH(mode):
  if mode == "_multiprocess":
    raise SkipTest("Fails due to mystery PicklingError.")
  n = max(2, default_num_samples())
  ripl = get_ripl(persistent_inference_trace=True)
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
  cdf = scipy.stats.norm(loc=1, scale=0.5**0.5).cdf
  return reportKnownContinuous(cdf, predictions, "N(1,sqrt(0.5))")

def testForEachParticleNoModeling():
  ripl = get_ripl()
  with assert_raises(Exception):
    ripl.infer("(for_each_particle (assume x (normal 0 1)))")
  ripl.assume("x", 0)
  eq_(0, ripl.sample("x"))
