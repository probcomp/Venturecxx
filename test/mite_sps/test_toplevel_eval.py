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

from venture.test.config import get_ripl
from venture.test.config import on_inf_prim

## adapted from test/development_milestones/test_no_inference.py

@on_inf_prim("none")
def testEvaluateConstantBool1():
  ripl = get_ripl()
  result = ripl.evaluate("true")
  assert result

@on_inf_prim("none")
def testEvaluateConstantBool2():
  ripl = get_ripl()
  result = ripl.evaluate("false")
  assert not result

@on_inf_prim("none")
def testEvaluateConstantNumber1():
  ripl = get_ripl()
  result = ripl.evaluate("1")
  assert_equal(result,1)

@on_inf_prim("none")
def testEvaluateConstantAtom1():
  ripl = get_ripl()
  result = ripl.evaluate("atom<5>")
  assert_equal(result,5)

@on_inf_prim("none")
def testEvaluateNumeric1():
  ripl = get_ripl()
  result = ripl.evaluate("(+ 3 4)")
  assert_equal(result,7)

@on_inf_prim("none")
def testEvaluateNumeric2():
  ripl = get_ripl()
  result = ripl.evaluate("(* 3 4)")
  assert_equal(result,12)

@on_inf_prim("none")
def testEvaluateNumeric3():
  ripl = get_ripl()
  result = ripl.evaluate("(pow 2 4)")
  assert_equal(result,16)

@on_inf_prim("none")
def testEvaluateCSP1():
  ripl = get_ripl()
  ripl.define("f","(lambda (x) x)")
  result = ripl.evaluate("(f (pow 2 4))")
  assert_equal(result,16)

@on_inf_prim("none")
def testEvaluateCSP2():
  ripl = get_ripl()
  ripl.define("f","(lambda (x) (pow x 4))")
  result = ripl.evaluate("(f 2)")
  assert_equal(result,16)

@on_inf_prim("none")
def testEvaluateCSP3():
  ripl = get_ripl()
  ripl.define("f","(lambda (x y) (* x y))")
  result = ripl.evaluate("(f 5 7)")
  assert_equal(result,35)

@on_inf_prim("none")
def testEvaluateCSP4():
  ripl = get_ripl()
  ripl.define("f","(lambda (x y z ) (* (+ x y) z))")
  result = ripl.evaluate("(f 2 3 5)")
  assert_equal(result,25)

@on_inf_prim("none")
def testEvaluateCSP5():
  ripl = get_ripl()
  ripl.define("f","(lambda (x) (+ x 1))")
  result = ripl.evaluate("(f (f (f (f (f 0)))))")
  assert_equal(result,5)

@on_inf_prim("none")
def testEvaluateCSP6():
  ripl = get_ripl()
  ripl.define("f","(lambda (x y) (+ x y 1))")
  result = ripl.evaluate("(f (f 2 3) (f 1 2))")
  assert_equal(result,11)

@on_inf_prim("none")
def testEvaluateArray1():
  ripl = get_ripl()
  ripl.define("xs","(array 2 3 5 7)")
  result = ripl.evaluate("(* (lookup xs 0) (lookup xs 1))")
  assert_equal(result,6)

@on_inf_prim("none")
def testEvaluatePair1():
  ripl = get_ripl()
  ripl.define("xs","(pair 2 (pair 3 nil))")
  result = ripl.evaluate("(* (first xs) (first (rest xs)))")
  assert_equal(result,6)

@on_inf_prim("none")
def testEvaluateList1():
  ripl = get_ripl()
  ripl.define("xs","(list 2 3 4)")
  result = ripl.evaluate("(* (lookup xs 1) (lookup xs 2))")
  assert_equal(result,12)
                    
