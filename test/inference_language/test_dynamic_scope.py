# Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

from nose.tools import assert_equal
from testconfig import config

from venture.test.config import gen_on_inf_prim
from venture.test.config import get_ripl
from venture.test.config import on_inf_prim
import venture.lite.value as vv

def count_nodes(ripl):
  scope = vv.VentureNumber(0)
  block = vv.VentureNumber(0)
  return ripl.sivm.core_sivm.engine.getDistinguishedTrace().numNodesInBlock(scope, block)

@on_inf_prim("none")
def testDynamicScope1():
  ripl = get_ripl()
  ripl.assume("x", "(normal 0.0 1.0)")
  ripl.predict("(tag 0 0 (normal x 1))")
  assert_equal(count_nodes(ripl), 1)
  assert_equal([2], ripl.infer("(num_blocks default)"))
  assert_equal([1], ripl.infer("(num_blocks 0)"))

@on_inf_prim("none")
def testDynamicScope2():
  ripl = get_ripl()
  ripl.assume("x", "(normal 0.0 1.0)")
  ripl.predict("(tag 0 0 (normal (normal x 1) 1))")
  assert_equal(count_nodes(ripl), 2)

@on_inf_prim("none")
def testDynamicScope3():
  ripl = get_ripl()
  ripl.assume("x", "(normal 0.0 1.0)")
  ripl.assume("f", "(lambda () (normal x 1.0))")
  ripl.predict("(tag 0 0 (normal (normal (f) 1) 1))")
  assert_equal(count_nodes(ripl), 3)

@on_inf_prim("none")
def testDynamicScope4():
  ripl = get_ripl()
  ripl.assume("x", "(normal 0.0 1.0)")
  ripl.assume("f", "(mem (lambda () (normal x 1.0)))")
  ripl.predict("(tag 0 0 (normal (+ (f) (normal (f) 1) (normal 0 1)) 1))")
  assert_equal(count_nodes(ripl), 4)

@on_inf_prim("none")
def testDynamicScope5():
  ripl = get_ripl()
  ripl.assume("x", "(tag 0 0 (normal 0.0 1.0))")
  ripl.assume("f", "(mem (lambda () (normal x 1.0)))")
  ripl.predict("(tag 0 0 (normal (+ (f) (normal (f) 1) (normal 0 1)) 1))")
  assert_equal(count_nodes(ripl), 5)

@on_inf_prim("none")
def testDynamicScope6():
  ripl = get_ripl()
  ripl.assume("x", "(normal 0.0 1.0)")
  ripl.assume("f", "(mem (lambda () (tag 0 1 (normal x 1.0))))")
  ripl.predict("(tag 0 0 (normal (+ (f) (normal (f) 1) (normal 0 1)) 1))")
  assert_equal(count_nodes(ripl), 3)

@on_inf_prim("none")
def testDynamicScope6a():
  ripl = get_ripl()
  ripl.assume("x", "(normal 0.0 1.0)")
  ripl.assume("f", "(mem (lambda () (tag 0 0 (normal x 1.0))))")
  ripl.predict("(tag 0 0 (normal (+ (f) (normal (f) 1) (normal 0 1)) 1))")
  assert_equal(count_nodes(ripl), 4)

@on_inf_prim("none")
def testDynamicScope7():
  ripl = get_ripl()
  ripl.assume("x", "(normal 0.0 1.0)")
  ripl.assume("f", "(mem (lambda () (tag 1 0 (normal x 1.0))))")
  ripl.predict("(tag 0 0 (normal (+ (f) (normal (f) 1) (normal 0 1)) 1))")
  assert_equal(count_nodes(ripl), 4)

@on_inf_prim("none")
def testDynamicScope8():
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("f","(mem (lambda () (tag 1 0 (normal x 1.0))))")
  ripl.assume("g","(lambda (z) (normal (+ (f) (tag 0 0 (normal (f) 1)) (normal z 1)) 1))")
  ripl.predict("(tag 0 0 (+ (g (bernoulli)) (g (bernoulli))))")
  assert_equal(count_nodes(ripl), 9)

@on_inf_prim("none")
def testTagExclude1():
  ripl = get_ripl()
  ripl.assume("f", "(mem (lambda (x) (tag_exclude 0 (bernoulli))))")
  ripl.predict("(tag 0 0 (+ (f 0) (f 1) (f 2) (f 3)))")
  assert_equal(count_nodes(ripl), 0)

@on_inf_prim("none")
def testTagExcludeBaseline():
  ripl = get_ripl()
  ripl.assume("f", "(mem (lambda (x) (bernoulli)))")
  ripl.predict("(tag 0 0 (+ (f 0) (f 1) (f 2) (f 3)))")
  assert_equal(count_nodes(ripl), 4)

@on_inf_prim("none")
def testArrayBlock():
  ripl = get_ripl()

  ripl.predict('(tag 1 (array 1 1) (flip))')

  ripl.infer('(mh 1 (array 1 1) 1)')

@gen_on_inf_prim("none")
def testCompoundBlockSerializing():
  for cons in ["array", "list", "pair", "vector"]:
    yield checkCompoundBlockSerializing, cons

def checkCompoundBlockSerializing(cons):
  ripl = get_ripl()
  ripl.infer("(resample_serializing 1)")
  ripl.assume('x', '(tag 1 (%s 1 1) (flip))' % cons)
  old_x = ripl.sample("x")
  for _ in range(20):
    ripl.infer('(mh 1 (%s 1 1) 1)' % cons)
    if ripl.sample("x") == old_x:
      continue
    else:
      return
  assert False, "MH did not move the choice it was supposed to operate on."

@on_inf_prim("none")
def testRandomBlockIdSmoke():
  # Test that scope membership maintenance works even if the block id
  # changes under inference
  r = get_ripl()
  if config["get_ripl"] == "puma":
    # Puma doesn't have the invariant check that Lite does
    r.define("checkInvariants", "(lambda () pass)")
  r.execute_program("""
  (predict (tag "frob" (flip) (flip)))
  (repeat 50
    (do (mh default one 1)
        (checkInvariants)))""")

@on_inf_prim("none")
def testRandomScopeIdSmoke():
  # Test that scope membership maintenance works even if the scope id
  # changes under inference
  r = get_ripl()
  if config["get_ripl"] == "puma":
    # Puma doesn't have the invariant check that Lite does
    r.define("checkInvariants", "(lambda () pass)")
  r.execute_program("""
  (predict (tag (flip) "frob" (flip)))
  (repeat 50
    (do (mh default one 1)
        (checkInvariants)))""")
