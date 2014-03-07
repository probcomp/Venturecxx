from venture.test.stats import statisticalTest, reportKnownDiscrete
from venture.test.config import get_ripl, collectSamples
from venture.ripl import Ripl
from nose.tools import eq_, assert_equal
from venture.lite.utils import cartesianProduct
from nose import SkipTest
from testconfig import config
import operator

def testArrayEquals():
  if config["get_ripl"] == "lite": raise SkipTest("Array equals not implemented in Lite")
    
  xs = reduce(operator.add,[cartesianProduct([[str(j) for j in range(2)] for i in range(k)]) for k in range(4)])
  ripl = get_ripl()
  for x in xs:
    for y in xs:
      checkArrayEquals(ripl,x,y)

def checkArrayEquals(ripl,x,y):
  assert_equal(ripl.sample("(eq (array %s) (array %s))" % (" ".join(x)," ".join(y))),x==y)

  
