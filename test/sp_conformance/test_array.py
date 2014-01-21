from venture.test.stats import *
from testconfig import config

class TestArrayExtended():
  def setup(self):
    self.ripl = config["get_ripl"]()
    self.ripl.assume("xs","(array 11 22 33)")

  def testLookup():
    assert self.ripl.predict("(lookup xs 0)")[1] == 11
    assert self.ripl.predict("(lookup xs 1)")[1] == 22
    assert self.ripl.predict("(lookup xs 2)")[1] == 33

  def testLength():
    assert self.ripl.predict("(size xs)")[1] == 3

  def testIsArray():
    assert self.ripl.predict("(is_array xs)")[1]
    assert self.ripl.predict("(is_array (array))")[1]
    assert not self.ripl.predict("(is_array (list 1 2))")[1]
    assert not self.ripl.predict("(is_array 0)")[1]


