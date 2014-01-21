from venture.shortcuts import *
from stat_helpers import *
from test_globals import N, globalKernel

def RIPL(): return make_lite_church_prime_ripl()

class TestListExtended():
  def setup(self):
    self.ripl = RIPL()
    self.ripl.assume("x1","(list)")
    self.ripl.assume("x2","(pair 1.0 x1)")
    self.ripl.assume("x3","(pair 2.0 x2)")
    self.ripl.assume("x4","(pair 3.0 x3)")
    self.ripl.assume("f","(lambda (x) (times x x x))")
    self.ripl.assume("y4","(map_list f x4)")

  def testFirst1():
    assert self.ripl.predict("(first y4)")[1] == 27.0

  def testLookup1():
    assert self.ripl.predict("(lookup y4 1)")[1] == 8.0

  def testLookup2():
    assert self.ripl.predict("(lookup (rest y4) 1)")[1] == 1.0

  def testIsPair1():
    assert not self.ripl.predict("(is_pair x1)")[1]

  def testIsPair2():
    assert self.ripl.predict("(is_pair x4)")[1]

  def testIsPair3():
    assert self.ripl.predict("(is_pair y4)")[1]

