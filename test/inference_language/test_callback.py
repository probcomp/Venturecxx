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

import numbers
from nose.tools import eq_

import venture.lite.value as v
from venture.test.config import get_ripl
from venture.engine.inference import Infer

def testCallbackSmoke():
  class MyCallback(object):
    def __init__(self):
      self.call_ct = 0
    def __call__(self, inferrer, *sampless):
      assert isinstance(inferrer, Infer)
      eq_(len(sampless), 2) # Two expressions
      for samples in sampless:
        eq_(len(samples), 4) # Four particles
        for sample in samples:
          assert isinstance(sample, dict) # A stack dict holding a number
          eq_(sample["type"], "number")
          assert isinstance(sample["value"], numbers.Number)
      self.call_ct += 1
  my_callback = MyCallback()

  ripl = get_ripl()
  ripl.bind_callback("foo", my_callback)
  ripl.execute_program("""
[infer (resample 4)]
[assume x (normal 0 1)]
[infer (repeat 3 (call_back foo x (gamma 1 1)))]""")
  eq_(my_callback.call_ct, 3)

def testCallbackReturns():
  ripl = get_ripl()
  ripl.bind_callback("three", lambda _inferrer: v.VentureNumber(3))
  ripl.infer("(do (x <- (call_back three)) (assert (eq 3 x)))")

def testDropIntoPythonSmoke():
  ripl = get_ripl()
  ripl.infer("(pyexec 'symbol<\"import venture.lite.value as vv\">)")
  eq_(3, ripl.infer("(pyeval 'symbol<\"vv.VentureNumber(3)\">)"))
