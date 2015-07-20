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

@on_inf_prim("gibbs")
def testStringScopeGibbs():
  """Check that using unnormalized values (like strings) as scope
  identifiers doesn't cause Gibbs to crash due to failed PMap
  lookup.
  """
  ripl = get_ripl()
  ripl.predict('(tag "z" 0 (flip))')
  ripl.infer('(gibbs "z" one 10)')
