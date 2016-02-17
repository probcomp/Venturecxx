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

@on_inf_prim("mh")
def testIf2():
  """This caused an earlier CXX implementation to crash because of a
  corner case of operators changing during inference."""
  ripl = get_ripl()
  ripl.assume('if1', '(if (bernoulli 0.5) biplex biplex)')
  ripl.assume('if2', '(if (bernoulli 0.5) if1 if1)')
  ripl.assume('if3', '(if (bernoulli 0.5) if2 if2)')
  ripl.assume('if4', '(if (bernoulli 0.5) if3 if3)')
  ripl.infer(20)
