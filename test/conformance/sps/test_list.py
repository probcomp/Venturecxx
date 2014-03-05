from nose.tools import eq_
from math import sin, cos
from venture.test.config import get_ripl
from nose import SkipTest
from nose.tools import assert_equal

def testList1():
  assert get_ripl().predict("(list)") == []

def testList2():
  assert get_ripl().predict("(list 1)") == [1.0]

def testList3():
  assert get_ripl().predict("(list 1 2)") == [1.0, 2.0]

def testPair1():
  assert get_ripl().predict("(pair 1 (list))") == [1.0]

def testIsPair1():
  assert not get_ripl().predict("(is_pair 1)")

def testIsPair2():
  assert not get_ripl().predict("(is_pair (list))")

def testIsPair3():
  assert get_ripl().predict("(is_pair (list 1))")

def testIsPair4():
  assert get_ripl().predict("(is_pair (pair 1 3))")

def testSize1():
  assert get_ripl().predict("(size (list))") == 0

def testSize2():
  assert get_ripl().predict("(size (list 4))") == 1

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

  def testFirst1(self):
    assert self.ripl.predict("(first x4)") == 3.0

  def testSecond1(self):
    assert self.ripl.predict("(second x4)") == 2.0

  def testRest1(self):
    assert_equal(self.ripl.predict("(rest x4)"),[2.0, 1.0])

  def testLookup1(self):
    assert self.ripl.predict("(lookup x4 1)") == 2.0

  def testLookup2(self):
    assert self.ripl.predict("(lookup (rest x4) 1)") == 1.0

  def testIsPair1(self):
    assert not self.ripl.predict("(is_pair x1)")

  def testIsPair2(self):
    assert self.ripl.predict("(is_pair x4)")

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
    self.ripl.assume("f","(lambda (x) (times x x x))")
    self.ripl.assume("y","(vmap_list f x)")

  def testFirst1(self):
    assert self.ripl.predict("(first y)") == 27.0

  def testLookup1(self):
    assert self.ripl.predict("(lookup y 1)") == 8.0

  def testLookup2(self):
    assert self.ripl.predict("(lookup (rest y) 1)") == 1.0

  def testIsPair3(self):
    assert self.ripl.predict("(is_pair y)")

  def testSize1(self):
    assert self.ripl.predict("(size y)") == 3

  def testMapOverListOfSPs(self):
    eq_(self.ripl.predict("(vmap_list (lambda (f) (f 1)) (list sin cos (lambda (x) (+ (* (sin x) (sin x)) (* (cos x) (cos x))))))"), [ sin(1), cos(1), 1])

class TestMapListExtended(object):
  _multiprocess_can_split_ = True
  def setup(self):
    raise SkipTest("map_list silly and not supported by puma")
    self.ripl = get_ripl()

    self.ripl.assume("x","(list 3.0 2.0 1.0)")
    self.ripl.assume("f","(lambda (x) (times x x x))")
    self.ripl.assume("y","(map_list f x)")

  def testFirst1(self):
    assert self.ripl.predict("(first y)") == 27.0

  def testLookup1(self):
    assert self.ripl.predict("(lookup y 1)") == 8.0

  def testLookup2(self):
    assert self.ripl.predict("(lookup (rest y) 1)") == 1.0

  def testIsPair3(self):
    assert self.ripl.predict("(is_pair y)")

  def testSize1(self):
    assert self.ripl.predict("(size y)") == 3

  def testMapOverListOfSPs(self):
    eq_(self.ripl.predict("(map_list (lambda (f) (f 1)) (list sin cos (lambda (x) (+ (* (sin x) (sin x)) (* (cos x) (cos x))))))"), [ sin(1), cos(1), 1])
