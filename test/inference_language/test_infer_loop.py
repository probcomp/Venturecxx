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

import time
import threading

from nose.tools import eq_
from flaky import flaky

from venture.test.config import get_ripl
from venture.test.config import on_inf_prim

@on_inf_prim("none")
def testStopSmoke():
  get_ripl().stop_continuous_inference()

def assertInferring(ripl):
  # If continuous inference is really running, the value of x should
  # change without me doing anything
  v = ripl.sample("x")
  time.sleep(0.00001) # Yield to give CI a chance to work
  assert not v == ripl.sample("x")

def assertNotInferring(ripl):
  # If not running continuous inference, sampling the same variable
  # always gives the same answer.
  v = ripl.sample("x")
  time.sleep(0.00001) # Yield to give CI a chance to work, if it's on
  assert v == ripl.sample("x")

@on_inf_prim("mh") # Really loop, but that's very special
def testInferLoopSmoke():
  ripl = get_ripl()
  ripl.assume("x", "(normal 0 1)")

  assertNotInferring(ripl)

  try:
    ripl.infer("(loop (mh default one 1))")
    assertInferring(ripl)
  finally:
    ripl.stop_continuous_inference() # Don't want to leave active threads lying around

@on_inf_prim("loop")
@flaky # Because sometimes it doesn't wait long enough for the other thread to go
def testStartStopInferLoop():
  numthreads = threading.active_count()
  ripl = get_ripl()
  eq_(numthreads, threading.active_count())
  ripl.assume("x", "(normal 0 1)")
  assertNotInferring(ripl)
  eq_(numthreads, threading.active_count())
  eq_(False, ripl.continuous_inference_status()['running'])
  try:
    ripl.infer("(loop (mh default one 1))")
    assertInferring(ripl)
    eq_(numthreads+1, threading.active_count())
    eq_(True, ripl.continuous_inference_status()['running'])
    with ripl.sivm._pause_continuous_inference():
      assertNotInferring(ripl)
      eq_(numthreads, threading.active_count())
      eq_(False, ripl.continuous_inference_status()['running'])
    assertInferring(ripl)
    eq_(numthreads+1, threading.active_count())
    eq_(True, ripl.continuous_inference_status()['running'])
  finally:
    ripl.stop_continuous_inference() # Don't want to leave active threads lying around

@on_inf_prim("loop")
def testStartCISmoke():
  ripl = get_ripl()
  ripl.assume("x", "(normal 0 1)")

  assertNotInferring(ripl)
  ripl.infer("(endloop)")
  assertNotInferring(ripl)

  try:
    ripl.start_continuous_inference("(mh default one 1)")
    assertInferring(ripl)
    ripl.infer("(endloop)")
    assertNotInferring(ripl)
  finally:
    ripl.stop_continuous_inference() # Don't want to leave active threads lying around

@on_inf_prim("loop")
def testRiplCommandInLoop():
  ripl = get_ripl()
  ripl.assume("x", "(normal 0 1)", label="foo")
  assertNotInferring(ripl)
  try:
    ripl.infer("(loop (do (forget 'foo) (assume x (normal 0 1) foo)))")
    assertInferring(ripl)
  finally:
    ripl.stop_continuous_inference() # Don't want to leave active threads lying around

@on_inf_prim("loop")
def testCrashStopsInferLoop():
  ripl = get_ripl()
  ripl.infer('(pyexec "import venture.lite.value as v")')
  ripl.infer('(pyexec "loop_thread_start_count = 0")')
  try:
    ripl.infer('(loop (do (pyexec "loop_thread_start_count += 1") crash))')
    time.sleep(0.00001) # Yield to give CI a chance to run and crash
    ripl.sample(1) # This should not restart a crashed CI thread
  finally:
    ripl.stop_continuous_inference() # Don't want to leave active threads lying around
  eq_(1, ripl.infer('(pyeval "v.VentureNumber(loop_thread_start_count)")'))
