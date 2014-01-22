from venture.test.stats import *
from testconfig import config

class TestListExtended():
  def setup(self):
    self.ripl = config["get_ripl"]()

    self.ripl.assume("vmap_list","""
(lambda (f xs)
  (if (is_pair xs)
      (pair (f (first xs)) (vmap_list f (rest xs)))
      xs))
""")

    self.ripl.assume("x1","(list)")
    self.ripl.assume("x2","(pair 1.0 x1)")
    self.ripl.assume("x3","(pair 2.0 x2)")
    self.ripl.assume("x4","(pair 3.0 x3)")
    self.ripl.assume("f","(lambda (x) (times x x x))")
    self.ripl.assume("y4","(vmap_list f x4)")

  def testFirst1(self):
    assert self.ripl.predict("(first y4)") == 27.0

  def testLookup1(self):
    assert self.ripl.predict("(lookup y4 1)") == 8.0

  def testLookup2(self):
    assert self.ripl.predict("(lookup (rest y4) 1)") == 1.0

  def testIsPair1(self):
    assert not self.ripl.predict("(is_pair x1)")

  def testIsPair2(self):
    assert self.ripl.predict("(is_pair x4)")

  def testIsPair3(self):
    assert self.ripl.predict("(is_pair y4)")


class TestMapListExtended():
  def setup(self):
    self.ripl = config["get_ripl"]()

    self.ripl.assume("x1","(list)")
    self.ripl.assume("x2","(pair 1.0 x1)")
    self.ripl.assume("x3","(pair 2.0 x2)")
    self.ripl.assume("x4","(pair 3.0 x3)")
    self.ripl.assume("f","(lambda (x) (times x x x))")
    self.ripl.assume("y4","(map_list f x4)")

  def testFirst1(self):
    assert self.ripl.predict("(first y4)") == 27.0

  def testLookup1(self):
    assert self.ripl.predict("(lookup y4 1)") == 8.0

  def testLookup2(self):
    assert self.ripl.predict("(lookup (rest y4) 1)") == 1.0

  def testIsPair1(self):
    assert not self.ripl.predict("(is_pair x1)")

  def testIsPair2(self):
    assert self.ripl.predict("(is_pair x4)")

  def testIsPair3(self):
    assert self.ripl.predict("(is_pair y4)")

