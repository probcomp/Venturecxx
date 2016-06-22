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

@on_inf_prim("none")
def testPredictInBlankTrace1():
  ripl = get_ripl()
  result = ripl.evaluate("(run_in (predict 1) (blank_trace))")
  assert_equal(result,1)

@on_inf_prim("none")
def testPredictInBlankTrace2():
  ripl = get_ripl()
  result = ripl.evaluate("(run_in (predict (+ 3 4)) (blank_trace))")
  assert_equal(result,7)

@on_inf_prim("none")
def testAssumeInBlankTrace1():
  ripl = get_ripl()
  result = ripl.evaluate("""\
(run_in (do (assume x 3)
            (assume y 4)
            (predict (* x y)))
        (blank_trace))
""")
  assert_equal(result,12)

@on_inf_prim("none")
def testLambdaInBlankTrace1():
  ripl = get_ripl()
  result = ripl.evaluate("""\
(run_in (do (assume f (lambda (x y) (+ x y 1)))
            (predict (f (f 2 3) (f 1 2))))
        (blank_trace))
""")
  assert_equal(result,11)
