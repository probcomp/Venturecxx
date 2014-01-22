from venture.test.stats import *
from testconfig import config

class TestArrayExtended():
  def setup(self):
    self.ripl = config["get_ripl"]()
    self.ripl.assume("xs","(array 11 22 33)")

  def testLookup(self):
    assert self.ripl.predict("(lookup xs 0)") == 11
    assert self.ripl.predict("(lookup xs 1)") == 22
    assert self.ripl.predict("(lookup xs 2)") == 33

  def testLength(self):
    assert self.ripl.predict("(size xs)") == 3

  def testIsArray(self):
    assert self.ripl.predict("(is_array xs)")
    assert self.ripl.predict("(is_array (array))")
    assert not self.ripl.predict("(is_array (list 1 2))")
    assert not self.ripl.predict("(is_array 0)")


