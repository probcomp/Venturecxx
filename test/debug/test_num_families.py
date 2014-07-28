from nose.tools import assert_equal

from venture.test.config import get_ripl, broken_in

@broken_in('lite', "numFamilies is only implemented in puma")
def testNumFamilies1():
  """A sanity test for numFamilies"""
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
