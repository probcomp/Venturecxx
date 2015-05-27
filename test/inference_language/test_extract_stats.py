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

from nose.tools import eq_

from venture.test.config import get_ripl, on_inf_prim

@on_inf_prim("extract_stats")
def testStatsExtractionSmoke():
  ripl = get_ripl()
  val = ripl.infer("""\
    (do
      (assume coin (make_beta_bernoulli 1 1))
      (observe (coin) true)
      (incorporate)
      (extract_stats coin))
""")
  eq_([1,0], val)
