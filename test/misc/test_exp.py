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

import numpy

from venture.test.config import get_ripl
from venture.test.config import on_inf_prim
import venture.value.dicts as v

@on_inf_prim("none")
def testVector():
  # Test that array-like objects don't get interpreted as expressions.
  ripl = get_ripl()
  ripl.predict(v.vector(numpy.array([1, 2])))
