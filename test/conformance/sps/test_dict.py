from venture.test.stats import *
from venture.test.config import get_ripl, collectSamples

# TODO
# This file contains one possibility for the Dictionary interface
# Note that "lookup" would be shared by arrays and "contains" would be 
# shared by sets. Also note the convention of using the data-structure name
# (i.e. "dict") as the constructor.
# I probably prefer (dict (list k1 v1) ... (list kN vN))
# but will leave it as is for now. It would not be hard to check the argument types
# and allow either.

@statisticalTest
def testDict1():
  ripl = get_ripl()

  ripl.assume("x","(bernoulli 1.0)")
  ripl.assume("d","""(dict (list (quote x) (quote y))
                           (list (normal 0.0 1.0) (normal 10.0 1.0)))""")
  ripl.predict("""(normal (plus
                           (lookup d (quote x))
                           (lookup d (quote y))
                           (lookup d (quote y)))
                         1.0)""")

  predictions = collectSamples(ripl,3)
  cdf = stats.norm(loc=20, scale=2).cdf
  return reportKnownContinuous("TestDict1", cdf, predictions, "N(20,2)")

def testDict2():
  ripl = get_ripl()
  ripl.assume("d","""(dict (list (quote x) (quote y))
                           (list (normal 0.0 1.0) (normal 10.0 1.0)))""")
  ripl.predict("(contains d (quote x))",label="p1")
  ripl.predict("(contains d (quote y))",label="p2")
  ripl.predict("(contains d (quote z))",label="p3")

  assert ripl.report("p1")
  assert ripl.report("p2")
  assert not ripl.report("p3")

def testDict3():
  ripl = get_ripl()
  ripl.assume("d","""(dict (list atom<1> atom<2>)
                           (list (normal 0.0 1.0) (normal 10.0 1.0)))""")
  ripl.predict("(contains d atom<1>)",label="p1")
  ripl.predict("(contains d atom<2>)",label="p2")
  ripl.predict("(contains d atom<3>)",label="p3")

  assert ripl.report("p1")
  assert ripl.report("p2")
  assert not ripl.report("p3")
