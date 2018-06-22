# Copyright (c) 2015 MIT Probabilistic Computing Project.
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

from venture.test.config import get_ripl
from venture.test.config import on_inf_prim

@on_inf_prim("none")
def testKeywordSmoke():
  r = get_ripl()
  r.execute_program("""
(assume x (normal loc: 0 scale: 1))
(resimulation_mh scope: default block: one 10)""")

@on_inf_prim("none")
def testKeywordSmokeVS():
  r = get_ripl()
  r.set_mode("venture_script")
  r.execute_program("""
assume x = normal(loc: 0, scale: 1);
resimulation_mh(scope: default, block: one, 10);""")
