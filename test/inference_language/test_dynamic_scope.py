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

from venture.test.config import get_ripl, on_inf_prim, broken_in

@on_inf_prim("none")
def testDynamicScope1():
  ripl = get_ripl()
  ripl.assume("x", "(normal 0.0 1.0)")
  ripl.predict("(tag 0 0 (normal x 1))")
  assert_equal(ripl.sivm.core_sivm.engine.getDistinguishedTrace().numNodesInBlock(0,0),1)

@on_inf_prim("none")
def testDynamicScope2():
  ripl = get_ripl()
  ripl.assume("x", "(normal 0.0 1.0)")
  ripl.predict("(tag 0 0 (normal (normal x 1) 1))")
  assert_equal(ripl.sivm.core_sivm.engine.getDistinguishedTrace().numNodesInBlock(0,0),2)

@on_inf_prim("none")
def testDynamicScope3():
  ripl = get_ripl()
  ripl.assume("x", "(normal 0.0 1.0)")
  ripl.assume("f", "(lambda () (normal x 1.0))")
  ripl.predict("(tag 0 0 (normal (normal (f) 1) 1))")
  assert_equal(ripl.sivm.core_sivm.engine.getDistinguishedTrace().numNodesInBlock(0,0),3)

@on_inf_prim("none")
def testDynamicScope4():
  ripl = get_ripl()
  ripl.assume("x", "(normal 0.0 1.0)")
  ripl.assume("f", "(mem (lambda () (normal x 1.0)))")
  ripl.predict("(tag 0 0 (normal (+ (f) (normal (f) 1) (normal 0 1)) 1))")
  assert_equal(ripl.sivm.core_sivm.engine.getDistinguishedTrace().numNodesInBlock(0,0),4)

@on_inf_prim("none")
def testDynamicScope5():
  ripl = get_ripl()
  ripl.assume("x", "(tag 0 0 (normal 0.0 1.0))")
  ripl.assume("f", "(mem (lambda () (normal x 1.0)))")
  ripl.predict("(tag 0 0 (normal (+ (f) (normal (f) 1) (normal 0 1)) 1))")
  assert_equal(ripl.sivm.core_sivm.engine.getDistinguishedTrace().numNodesInBlock(0,0),5)

@on_inf_prim("none")
def testDynamicScope6():
  ripl = get_ripl()
  ripl.assume("x", "(normal 0.0 1.0)")
  ripl.assume("f", "(mem (lambda () (tag 0 1 (normal x 1.0))))")
  ripl.predict("(tag 0 0 (normal (+ (f) (normal (f) 1) (normal 0 1)) 1))")
  assert_equal(ripl.sivm.core_sivm.engine.getDistinguishedTrace().numNodesInBlock(0,0),3)

@on_inf_prim("none")
def testDynamicScope6a():
  ripl = get_ripl()
  ripl.assume("x", "(normal 0.0 1.0)")
  ripl.assume("f", "(mem (lambda () (tag 0 0 (normal x 1.0))))")
  ripl.predict("(tag 0 0 (normal (+ (f) (normal (f) 1) (normal 0 1)) 1))")
  assert_equal(ripl.sivm.core_sivm.engine.getDistinguishedTrace().numNodesInBlock(0,0),4)

@on_inf_prim("none")
def testDynamicScope7():
  ripl = get_ripl()
  ripl.assume("x", "(normal 0.0 1.0)")
  ripl.assume("f", "(mem (lambda () (tag 1 0 (normal x 1.0))))")
  ripl.predict("(tag 0 0 (normal (+ (f) (normal (f) 1) (normal 0 1)) 1))")
  assert_equal(ripl.sivm.core_sivm.engine.getDistinguishedTrace().numNodesInBlock(0,0),4)

@on_inf_prim("none")
def testDynamicScope8():
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("f","(mem (lambda () (tag 1 0 (normal x 1.0))))")
  ripl.assume("g","(lambda (z) (normal (+ (f) (tag 0 0 (normal (f) 1)) (normal z 1)) 1))")
  ripl.predict("(tag 0 0 (+ (g (bernoulli)) (g (bernoulli))))")
  assert_equal(ripl.sivm.core_sivm.engine.getDistinguishedTrace().numNodesInBlock(0,0),9)

@on_inf_prim("none")
def testTagExclude1():
  ripl = get_ripl()
  ripl.assume("f", "(mem (lambda (x) (tag_exclude 0 (bernoulli))))")
  ripl.predict("(tag 0 0 (+ (f 0) (f 1) (f 2) (f 3)))")
  assert_equal(ripl.sivm.core_sivm.engine.getDistinguishedTrace().numNodesInBlock(0, 0), 0)

@on_inf_prim("none")
def testTagExcludeBaseline():
  ripl = get_ripl()
  ripl.assume("f", "(mem (lambda (x) (bernoulli)))")
  ripl.predict("(tag 0 0 (+ (f 0) (f 1) (f 2) (f 3)))")
  assert_equal(ripl.sivm.core_sivm.engine.getDistinguishedTrace().numNodesInBlock(0, 0), 4)

@on_inf_prim("none")
@broken_in('puma', "puma can't handle arrays as blocks in a tag.")
def testArrayBlock():
  ripl = get_ripl()

  ripl.predict('(tag 1 (array 1 1) (flip))')

  ripl.infer('(mh 1 (array 1 1) 1)')

@on_inf_prim("none")
@broken_in('puma', "puma can't handle arrays as blocks in a tag.")
def testArrayBlockSerializing():
  ripl = get_ripl()
  ripl.infer("(resample_serializing 1)")
  ripl.assume('x', '(tag 1 (array 1 1) (flip))')
  old_x = ripl.sample("x")
  for _ in range(20):
    ripl.infer('(mh 1 (array 1 1) 1)')
    if ripl.sample("x") == old_x:
      continue
    else:
      return
  assert False, "MH did not move the choice it was supposed to operate on."
