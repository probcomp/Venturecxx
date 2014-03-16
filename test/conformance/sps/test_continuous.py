from nose.tools import eq_
from venture.test.config import get_ripl

def testMVGaussSmoke():
  eq_(get_ripl().predict("(is_array (multivariate_normal (array 1 2) (matrix (list (list 3 4) (list 5 6)))))"), True)
