from nose.tools import raises

from venture.test.config import get_ripl, on_inf_prim

@on_inf_prim("none")
def testAssertSmoke():
  get_ripl().infer("(assert true)")

@on_inf_prim("none")
@raises(AssertionError)
def testAssertSmoke2():
  get_ripl().infer("(assert false)")


