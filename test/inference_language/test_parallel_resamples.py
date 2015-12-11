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

import threading

from nose.tools import eq_
from nose import SkipTest

from venture.test.config import default_num_samples
from venture.test.config import gen_on_inf_prim
from venture.test.config import get_ripl
from venture.test.config import on_inf_prim
from venture.test.stats import reportKnownGaussian
from venture.test.stats import statisticalTest

@gen_on_inf_prim("resample")
def testSynchronousIsSerial():
  yield checkSynchronousIsSerial, "resample"
  yield checkSynchronousIsSerial, "resample_serializing"

def checkSynchronousIsSerial(mode):
  numthreads = threading.active_count()
  r = get_ripl()
  eq_(numthreads, threading.active_count())
  r.infer("(%s 2)" % mode)
  eq_(numthreads, threading.active_count())

@gen_on_inf_prim("resample")
def testResamplingSmoke():
  for mode in ["", "_serializing", "_threaded", "_thread_ser", "_multiprocess"]:
    yield checkResamplingSmoke, mode

@statisticalTest
def checkResamplingSmoke(mode):
  n = default_num_samples()
  r = get_ripl()
  r.infer("(resample%s %s)" % (mode, n))
  stack_dicts = r.sivm.core_sivm.engine.sample_all(r._ensure_parsed_expression("(normal 0 1)"))
  predictions = [d["value"] for d in stack_dicts]
  return reportKnownGaussian(0, 1, predictions)

@on_inf_prim("resample")
def testResamplingSmoke2():
  r = get_ripl()
  r.infer("(resample_multiprocess 10 3)") # Limit the number of processes
  # TODO How can I check that the number of processes was actually limited?
  r.predict("(normal 0 1)") # Check that the resulting configuration doesn't blow up instantly

@on_inf_prim("resample")
def testResamplingSmoke3():
  r = get_ripl()
  r.infer("(resample_multiprocess 3 3)") # Limit the number of processes
  # TODO How can I check that the number of processes was actually limited?
  r.predict("(normal 0 1)") # Check that the resulting configuration doesn't blow up instantly

@statisticalTest
@on_inf_prim("resample")
def testResamplingSmoke4():
  "Check that limiting the number of processes doesn't screw up inference too much."
  n = default_num_samples()
  r = get_ripl()
  r.infer("(resample_multiprocess %s %s)" % (n, n/2)) # Limit the number of processes
  predictions = r.sample_all("(normal 0 1)")
  eq_(n, len(predictions))
  return reportKnownGaussian(0, 1, predictions)

@on_inf_prim("resample_serializing")
def testSerializingTracesWithRandomSPs():
  "Check that the presence of random variables that are SPs does not mess up resampling."
  raise SkipTest("Still can't serialize random SPs")
  r = get_ripl()
  r.infer("(resample_serializing 2)")
  r.assume("foo", "(categorical (simplex 0.5 0.5) (array (lambda () 1) (lambda () 2)))")
  r.infer("(resample_serializing 2)")
