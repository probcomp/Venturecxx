from nose import SkipTest
from testconfig import config
from venture.test.config import get_ripl
from nose.tools import assert_equal

def testNumFamilies1():
  """A sanity test for numFamilies"""
  if config["get_ripl"] != "puma": raise SkipTest("numFamilies only implemented in puma")
  ripl = get_ripl()
  ripl.assume("rain","(bernoulli 0.2)")
  ripl.assume("sprinkler","(if rain (bernoulli 0.01) (bernoulli 0.4))")
  ripl.assume("grassWet","""
(if rain
  (if sprinkler (bernoulli 0.99) (bernoulli 0.8))
  (if sprinkler (bernoulli 0.9)  (bernoulli 0.00001)))
""")
  ripl.observe("grassWet", True)

  numFamilies = ripl.sivm.core_sivm.engine.getDistinguishedTrace().numFamilies()
  assert_equal(numFamilies,[4,1,1,1])
