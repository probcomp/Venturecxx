from nose.tools import eq_
from venture.test.config import get_ripl

def testSymDirSmoke1():
  eq_(get_ripl().predict("(is_simplex (symmetric_dirichlet 3 4))"), True)
