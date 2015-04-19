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

from venture.test.config import in_backend
from venture.lite.value import VentureNumber
from venture.lite.mlens import real_lenses

@in_backend("none")
def testLensSmoke1():
  v1 = VentureNumber(3)
  v2 = VentureNumber(4)
  lenses = real_lenses([v1, [v2]])
  assert [lens.get() for lens in lenses] == [3,4]
  lenses[1].set(2)
  assert [lens.get() for lens in lenses] == [3,2]
  assert v2.number == 2
