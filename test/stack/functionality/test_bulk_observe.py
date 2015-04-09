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
from nose.tools import eq_

@on_inf_prim("mh")
def testBulkObserve1():
  ripl = get_ripl()
  n_before = len(ripl.list_directives())
  ripl.observe_dataset("normal",[([0,5],11),([2,8],22),([3,10],33)],label="pid")
  ripl.infer(100)
  eq_(ripl.report("pid_0"),11)
  eq_(ripl.report("pid_1"),22)
  eq_(ripl.report("pid_2"),33)
  n_after = len(ripl.list_directives())
  eq_(n_after, n_before + 3)
