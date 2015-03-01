from nose.tools import eq_

from venture.test.config import get_ripl, broken_in, on_inf_prim

@on_inf_prim("none")
def testFreezeSanityCheck1():
  ripl = get_ripl()

  ripl.assume("x", "(normal 0.0 1.0)")
  ripl.assume("y", "(normal (normal (normal (normal (normal x 1.0) 1.0) 1.0) 1.0) 1.0)")

  engine = ripl.sivm.core_sivm.engine
  eq_(engine.get_entropy_info()["unconstrained_random_choices"],6)

  ripl.freeze(2)
  eq_(engine.get_entropy_info()["unconstrained_random_choices"],1)

@on_inf_prim("none")
def testFreezeSanityCheck2():
  ripl = get_ripl()

  ripl.assume("x", "(normal 0.0 1.0)")
  ripl.assume("y", "(scope_include 0 0 (normal (normal (normal (normal (normal x 1.0) 1.0) 1.0) 1.0) 1.0))")
  ripl.assume("ringer", "(scope_include 0 0 (normal 0.0 1.0))")

  engine = ripl.sivm.core_sivm.engine
  eq_(engine.getDistinguishedTrace().numNodesInBlock(0,0),6)

  ripl.freeze(2)
  eq_(engine.getDistinguishedTrace().numNodesInBlock(0,0),1)

@on_inf_prim("mh")
def testFreezeSanityCheck3():
  """Check that a frozen value no longer changes under inference, even
though unfrozen ones do."""
  ripl = get_ripl()
  ripl.assume("x", "(normal 0.0 1.0)")
  ripl.assume("y", "(normal 0.0 1.0)")
  xval = ripl.sample("x")
  yval = ripl.sample("y")
  ripl.freeze(1)
  ripl.infer(100)
  eq_(xval, ripl.sample("x"))
  assert not yval == ripl.sample("y")
