# Copyright (c) 2014 MIT Probabilistic Computing Project.
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
from math import sin, cos
from venture.test.config import get_ripl, on_inf_prim
from nose.tools import assert_equal

@on_inf_prim("none")
def testList1():
  assert get_ripl().predict("(list)") == []

@on_inf_prim("none")
def testList2():
  assert get_ripl().predict("(list 1)") == [1.0]

@on_inf_prim("none")
def testList3():
  assert get_ripl().predict("(list 1 2)") == [1.0, 2.0]

@on_inf_prim("none")
def testPair1():
  assert get_ripl().predict("(pair 1 (list))") == [1.0]

@on_inf_prim("none")
def testIsPair1():
  assert not get_ripl().predict("(is_pair 1)")

@on_inf_prim("none")
def testIsPair2():
  assert not get_ripl().predict("(is_pair (list))")

@on_inf_prim("none")
def testIsPair3():
  assert get_ripl().predict("(is_pair (list 1))")

@on_inf_prim("none")
def testIsPair4():
  assert get_ripl().predict("(is_pair (pair 1 3))")

@on_inf_prim("none")
def testSize1():
  assert get_ripl().predict("(size (list))") == 0

@on_inf_prim("none")
def testSize2():
  assert get_ripl().predict("(size (list 4))") == 1

@on_inf_prim("none")
def testSize3():
  assert get_ripl().predict("(size (pair 3 (list 4)))") == 2

class TestList(object):
  _multiprocess_can_split_ = True
  def setup(self):
    self.ripl = get_ripl()

    self.ripl.assume("x1","(list)")
    self.ripl.assume("x2","(pair 1.0 x1)")
    self.ripl.assume("x3","(pair 2.0 x2)")
    self.ripl.assume("x4","(pair 3.0 x3)")

  @on_inf_prim("none")
  def testFirst1(self):
    assert self.ripl.predict("(first x4)") == 3.0

  @on_inf_prim("none")
  def testSecond1(self):
    assert self.ripl.predict("(second x4)") == 2.0

  @on_inf_prim("none")
  def testRest1(self):
    assert_equal(self.ripl.predict("(rest x4)"),[2.0, 1.0])

  @on_inf_prim("none")
  def testLookup1(self):
    assert self.ripl.predict("(lookup x4 1)") == 2.0

  @on_inf_prim("none")
  def testLookup2(self):
    assert self.ripl.predict("(lookup (rest x4) 1)") == 1.0

  @on_inf_prim("none")
  def testIsPair1(self):
    assert not self.ripl.predict("(is_pair x1)")

  @on_inf_prim("none")
  def testIsPair2(self):
    assert self.ripl.predict("(is_pair x4)")

  @on_inf_prim("none")
  def testSize1(self):
    assert self.ripl.predict("(size x4)") == 3

class TestListExtended(object):
  _multiprocess_can_split_ = True
  def setup(self):
    self.ripl = get_ripl()

    self.ripl.assume("vmap_list","""
(lambda (f xs)
  (if (is_pair xs)
      (pair (f (first xs)) (vmap_list f (rest xs)))
      xs))
""")

    self.ripl.assume("x","(list 3.0 2.0 1.0)")
    self.ripl.assume("f","(lambda (x) (* x x x))")
    self.ripl.assume("y","(vmap_list f x)")

  @on_inf_prim("none")
  def testFirst1(self):
    assert self.ripl.predict("(first y)") == 27.0

  @on_inf_prim("none")
  def testLookup1(self):
    assert self.ripl.predict("(lookup y 1)") == 8.0

  @on_inf_prim("none")
  def testLookup2(self):
    assert self.ripl.predict("(lookup (rest y) 1)") == 1.0

  @on_inf_prim("none")
  def testIsPair3(self):
    assert self.ripl.predict("(is_pair y)")

  @on_inf_prim("none")
  def testSize1(self):
    assert self.ripl.predict("(size y)") == 3

  @on_inf_prim("none")
  def testMapOverListOfSPs(self):
    eq_(self.ripl.predict("(vmap_list (lambda (f) (f 1)) (list sin cos (lambda (x) (+ (* (sin x) (sin x)) (* (cos x) (cos x))))))"), [ sin(1), cos(1), 1])

