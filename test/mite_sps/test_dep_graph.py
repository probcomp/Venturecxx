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

from nose.tools import assert_equal, assert_not_equal

from venture.test.config import get_ripl
from venture.test.config import on_inf_prim

@on_inf_prim("none")
def testESREdge():
  ripl = get_ripl()
  result = ripl.evaluate("""\
(run_in
 (do (assume x (normal 0 1))
     (assume y ((lambda () x)))
     (predict (list x y))
     (xy <- (value_at (toplevel 3)))
     (s <- (single_site_subproblem (toplevel 1)))
     (p <- (extract s))
     (regen s (rest p))
     (xy_ <- (value_at (toplevel 3)))
     (return (list xy xy_)))
 (graph_trace))
""")
  (x, y), (x_, y_) = result
  assert_equal(x, y)
  assert_not_equal(x, x_)
  assert_equal(x_, y_)

@on_inf_prim("none")
def testRecursion():
  ripl = get_ripl()
  result = ripl.evaluate("""\
(run_in
 (do (assume x (normal 0 1))
     (assume f (lambda (i) (if (= i 0) x (f (- i 1)))))
     (assume y (f 2))
     (predict (list x y))
     (xy <- (value_at (toplevel 4)))
     (s <- (single_site_subproblem (toplevel 1)))
     (p <- (extract s))
     (regen s (rest p))
     (xy_ <- (value_at (toplevel 4)))
     (return (list xy xy_)))
 (graph_trace))
""")
  (x, y), (x_, y_) = result
  assert_equal(x, y)
  assert_not_equal(x, x_)
  assert_equal(x_, y_)
