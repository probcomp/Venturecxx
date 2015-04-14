# Copyright (c) 2013, 2014 MIT Probabilistic Computing Project.
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

@on_inf_prim("mh")
def testTrig1():
  "Simple test that verifies sin^2 + cos^2 = 1 as x varies"
  ripl = get_ripl()
  ripl.assume("sq","(lambda (x) (* x x))")
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("a","(sq (sin x))")
  ripl.assume("b","(sq (cos x))")
  ripl.predict("(+ a b)",label="pid")
  for _ in range(10):
    ripl.infer(1)
    assert abs(ripl.report("pid") - 1) < .001
