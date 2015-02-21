from nose.tools import eq_

from venture.test.config import get_ripl, on_inf_prim

@on_inf_prim("emap")
def testEMAPSmoke():
  ripl = get_ripl()
  ripl.assume("c", "(flip 0.1)")
  ripl.observe("(if c (flip 0.99) (flip 0.01))", True)
  ripl.infer("(emap default all 1)")
  eq_(True, ripl.sample("c"))
