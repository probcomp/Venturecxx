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

import operator
from nose.tools import eq_

from venture.lite.utils import cartesianProduct
from venture.test.config import get_ripl, on_inf_prim

@on_inf_prim("none")
def testArrayEquals():
  xs = reduce(operator.add,[cartesianProduct([[str(j) for j in range(2)] for _ in range(k)]) for k in range(4)])
  ripl = get_ripl()
  for x in xs:
    for y in xs:
      checkArrayEquals(ripl,x,y)

def checkArrayEquals(ripl,x,y):
  eq_(ripl.sample("(eq (array %s) (array %s))" % (" ".join(x)," ".join(y))), x==y)

  
