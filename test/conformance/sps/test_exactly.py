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

from venture.test.config import get_ripl, on_inf_prim
from nose.tools import assert_equal

@on_inf_prim("none")
def testExactly1():
  ripl = get_ripl()
  
  ripl.observe('(exactly 0 -1)', 0.0)
  ripl.infer('(incorporate)')
  
  assert_equal(ripl.get_global_logscore(), 0)

@on_inf_prim("none")
def testExactly2():
  ripl = get_ripl()
  
  ripl.observe('(exactly 0 -1)', 1.0)
  ripl.infer('(incorporate)')
  
  assert_equal(ripl.get_global_logscore(), -1)

