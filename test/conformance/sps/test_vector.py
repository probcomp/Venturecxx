# Copyright (c) 2017 MIT Probabilistic Computing Project.
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

def test_append():
  ripl = get_ripl(init_mode='venture_script')
  ripl.assume('a', '[1,2,3]')
  ripl.assume('b', '[4,5,6]')
  assert ripl.sample('append(a, b)') == [1,2,3,4,5,6]
