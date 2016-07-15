# Copyright (c) 2016 MIT Probabilistic Computing Project.
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

from nose.tools import eq_

from venture.test.config import get_ripl

def testSmoke():
  r = get_ripl()
  r.assume("a", "(tag 0 0 (normal 0 1))")
  r.assume("b", "(tag 0 1 (normal 0 1))")
  r.force("a", 1)
  r.force("b", 2)
  def both(ans):
      assert (ans == [1, 2] or ans == [2, 1])
  both(r.infer("""(do
  (s <- (select (minimal_subproblem (by_extent (by_top)))))
  (get_current_values s))"""))
  eq_([2], r.infer("""(do
  (s <- (select (minimal_subproblem (by_tag_value 0 1))))
  (get_current_values s))"""))
  both(r.infer("""(do
  (s <- (select (minimal_subproblem (by_tag 0))))
  (get_current_values s))"""))
