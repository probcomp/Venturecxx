from testconfig import config
from nose import SkipTest
from venture.test.config import get_ripl
from nose.tools import eq_

def testFreezeSanityCheck1():
  if config["get_ripl"] != "puma": raise SkipTest("Freeze only implemented in puma")

  ripl = get_ripl()

  ripl.assume("x", "(normal 0.0 1.0)")
  ripl.assume("y", "(normal (normal (normal (normal (normal x 1.0) 1.0) 1.0) 1.0) 1.0)")

  engine = ripl.sivm.core_sivm.engine
  eq_(engine.get_entropy_info()["unconstrained_random_choices"],6)

  engine.getDistinguishedTrace().freeze(2)
  eq_(engine.get_entropy_info()["unconstrained_random_choices"],1)

def testFreezeSanityCheck2():
  if config["get_ripl"] != "puma": raise SkipTest("Freeze only implemented in puma")

  ripl = get_ripl()

  ripl.assume("x", "(normal 0.0 1.0)")
  ripl.assume("y", "(scope_include 0 0 (normal (normal (normal (normal (normal x 1.0) 1.0) 1.0) 1.0) 1.0))")
  ripl.assume("ringer", "(scope_include 0 0 (normal 0.0 1.0))")

  engine = ripl.sivm.core_sivm.engine
  eq_(engine.getDistinguishedTrace().numNodesInBlock(0,0),6)

  engine.getDistinguishedTrace().freeze(2)
  eq_(engine.getDistinguishedTrace().numNodesInBlock(0,0),1)


