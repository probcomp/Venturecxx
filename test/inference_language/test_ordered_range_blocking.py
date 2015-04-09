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

from venture.test.config import get_ripl, on_inf_prim

@on_inf_prim("pgibbs")
def testOrderedRangeBlockingExample():
  ripl = get_ripl()
  ripl.assume("a", "(tag 0 0 (normal 0.0 1.0))", label="a")
  ripl.assume("b", "(tag 0 1 (normal 1.0 1.0))", label="b")
  ripl.assume("c", "(tag 0 2 (normal 2.0 1.0))", label="c")
  ripl.assume("d", "(tag 0 3 (normal 3.0 1.0))", label="d")
  olda = ripl.report("a")
  oldb = ripl.report("b")
  oldc = ripl.report("c")
  oldd = ripl.report("d")
  # Should change b and c.
  ripl.infer("(pgibbs 0 (ordered_range 1 2) 10 3)")
  newa = ripl.report("a")
  newb = ripl.report("b")
  newc = ripl.report("c")
  newd = ripl.report("d")
  assert olda == newa
  assert not oldb == newb
  assert not oldc == newc
  assert oldd == newd

