from nose.tools import eq_
from venture.test.config import get_ripl, on_inf_prim

# TODO AXCH why is this a test? Why shouldn't it be legal to start at 0?
@on_inf_prim("none")
def testCRPSmoke():
  eq_(get_ripl().predict("((make_crp 1.0))"), 1)
