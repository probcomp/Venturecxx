# Copyright (c) 2014 MIT Probabilistic Computing Project.
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

from venture.test.config import get_ripl
from venture.test.config import on_inf_prim

@on_inf_prim("none")
def testPredictConstantBool1():
  ripl = get_ripl()
  ripl.predict("true",label="pid")
  assert ripl.report("pid")

@on_inf_prim("none")
def testPredictConstantBool2():
  ripl = get_ripl()
  ripl.predict("false",label="pid")
  assert not ripl.report("pid")

@on_inf_prim("none")
def testPredictConstantNumber1():
  ripl = get_ripl()
  ripl.predict("1",label="pid")
  assert_equal(ripl.report("pid"),1)

@on_inf_prim("none")
def testPredictConstantAtom1():
  ripl = get_ripl()
  ripl.predict("atom<5>",label="pid")
  assert_equal(ripl.report("pid"),5)

@on_inf_prim("none")
def testPredictNumeric1():
  ripl = get_ripl()
  ripl.predict("(+ 3 4)",label="pid")
  assert_equal(ripl.report("pid"),7)

@on_inf_prim("none")
def testPredictNumeric2():
  ripl = get_ripl()
  ripl.predict("(* 3 4)",label="pid")
  assert_equal(ripl.report("pid"),12)

@on_inf_prim("none")
def testPredictNumeric3():
  ripl = get_ripl()
  ripl.predict("(pow 2 4)",label="pid")
  assert_equal(ripl.report("pid"),16)

@on_inf_prim("none")
def testPredictCSP1():
  ripl = get_ripl()
  ripl.assume("f","(lambda (x) x)")
  ripl.predict("(f (pow 2 4))",label="pid")
  assert_equal(ripl.report("pid"),16)

@on_inf_prim("none")
def testPredictCSP2():
  ripl = get_ripl()
  ripl.assume("f","(lambda (x) (pow x 4))")
  ripl.predict("(f 2)",label="pid")
  assert_equal(ripl.report("pid"),16)

@on_inf_prim("none")
def testPredictCSP3():
  ripl = get_ripl()
  ripl.assume("f","(lambda (x y) (* x y))")
  ripl.predict("(f 5 7)",label="pid")
  assert_equal(ripl.report("pid"),35)

@on_inf_prim("none")
def testPredictCSP4():
  ripl = get_ripl()
  ripl.assume("f","(lambda (x y z ) (* (+ x y) z))")
  ripl.predict("(f 2 3 5)",label="pid")
  assert_equal(ripl.report("pid"),25)

@on_inf_prim("none")
def testPredictCSP5():
  ripl = get_ripl()
  ripl.assume("f","(lambda (x) (+ x 1))")
  ripl.predict("(f (f (f (f (f 0)))))",label="pid")
  assert_equal(ripl.report("pid"),5)

@on_inf_prim("none")
def testPredictCSP6():
  ripl = get_ripl()
  ripl.assume("f","(lambda (x y) (+ x y 1))")
  ripl.predict("(f (f 2 3) (f 1 2))",label="pid")
  assert_equal(ripl.report("pid"),11)

@on_inf_prim("none")
def testPredictArray1():
  ripl = get_ripl()
  ripl.assume("xs","(array 2 3 5 7)")
  ripl.predict("(* (lookup xs 0) (lookup xs 1))",label="pid")
  assert_equal(ripl.report("pid"),6)

@on_inf_prim("none")
def testPredictPair1():
  ripl = get_ripl()
  ripl.assume("xs","(pair 2 (pair 3 nil))")
  ripl.predict("(* (first xs) (first (rest xs)))",label="pid")
  assert_equal(ripl.report("pid"),6)

@on_inf_prim("none")
def testPredictList1():
  ripl = get_ripl()
  ripl.assume("xs","(list 2 3 4)")
  ripl.predict("(* (lookup xs 1) (lookup xs 2))",label="pid")
  assert_equal(ripl.report("pid"),12)
                    
