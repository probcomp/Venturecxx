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

from venture.test.config import get_ripl
from venture.test.config import on_inf_prim

@on_inf_prim("none")
def testRepeatZeroTimes():
  r = get_ripl()
  r.assume("x", "(normal 0 1)")
  x_old = r.sample("x")
  r.infer("(repeat 0 (resimulation_mh default one 1))")
  x_new = r.sample("x")
  assert x_old == x_new, "Repeat zero times did it anyway."
