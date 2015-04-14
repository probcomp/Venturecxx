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

from venture.test.config import get_ripl, gen_on_inf_prim

@gen_on_inf_prim("pgibbs")
def testBrushScopePGibbs():
  yield checkBrushScope, "pgibbs"

@gen_on_inf_prim("func_pgibbs")
def testBrushScopeFuncPGibbs():
  yield checkBrushScope, "func_pgibbs"

def checkBrushScope(operator):
  """Check that putting scope control in the brush doesn't cause
  particle Gibbs to crash."""
  ripl = get_ripl()
  ripl.assume("x1", "(tag (quote state) 0 (normal 1 1))")
  ripl.assume("t", "1") # This variable matters to get the block id into the brush.
  ripl.assume("x2", """
(if (> x1 1)
    (tag (quote state) t (normal 2 1))
    (tag (quote state) t (normal 0 1)))
""")
  ripl.infer("(%s state ordered 4 3)" % operator)
