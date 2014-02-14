from nose.tools import eq_
from venture.test.config import get_ripl

def testCRPSmoke():
  eq_(get_ripl().predict("((make_crp 1.0))"), 1)
