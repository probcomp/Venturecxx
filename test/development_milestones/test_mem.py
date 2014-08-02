from venture.test.config import get_ripl, on_inf_prim
from nose.tools import eq_

@on_inf_prim("none")
def testMem1():
  ripl = get_ripl()
  ripl.assume('f', '(mem flip)')
  flip1 = ripl.predict('(f)')
  flip2 = ripl.predict('(f)')
  eq_(flip1, flip2)
