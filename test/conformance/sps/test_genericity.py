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

from nose.tools import eq_
from numpy.testing import assert_allclose
from venture.test.config import get_ripl, collectSamples, on_inf_prim

def testGenericPlusSmoke():
  eq_(3, get_ripl().evaluate("(+ 1 2)"))
  assert_allclose([5, 9], get_ripl().evaluate("(+ (vector 1 2) (vector 4 7))"))

def testGenericTimesSmoke():
  assert_allclose([3, 6], get_ripl().evaluate("(* 3 (vector 1 2))"))
  assert_allclose([8, 14], get_ripl().evaluate("(* (vector 4 7) 2)"))

def testGenericNormalSmoke():
  get_ripl().evaluate("(normal (vector 1 2 3) 3)")
  get_ripl().evaluate("(normal 3 (vector 1 2 3))")
  get_ripl().evaluate("(normal (vector 1 2 3) (vector 1 2 3))")
  assert_allclose(get_ripl().evaluate("(assess (vector 0 0) normal (vector 1 2) 3)"),
                  get_ripl().evaluate("(assess 0 normal 1 3)") +
                  get_ripl().evaluate("(assess 0 normal 2 3)"))
  assert_allclose(get_ripl().evaluate("(assess (vector 0 0) normal 3 (vector 1 2))"),
                  get_ripl().evaluate("(assess 0 normal 3 1)") +
                  get_ripl().evaluate("(assess 0 normal 3 2)"))
  assert_allclose(get_ripl().evaluate("(assess (vector 0 0) normal (vector 1 2) (vector 1 2))"),
                  get_ripl().evaluate("(assess 0 normal 1 1)") +
                  get_ripl().evaluate("(assess 0 normal 2 2)"))
