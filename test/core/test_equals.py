import operator
from nose.tools import eq_

from venture.lite.utils import cartesianProduct
from venture.test.config import get_ripl

def testArrayEquals():
  xs = reduce(operator.add,[cartesianProduct([[str(j) for j in range(2)] for _ in range(k)]) for k in range(4)])
  ripl = get_ripl()
  for x in xs:
    for y in xs:
      checkArrayEquals(ripl,x,y)

def checkArrayEquals(ripl,x,y):
  eq_(ripl.sample("(eq (array %s) (array %s))" % (" ".join(x)," ".join(y))), x==y)

  
