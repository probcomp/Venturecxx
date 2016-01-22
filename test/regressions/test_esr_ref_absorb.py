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

from venture.test.config import collectSamples
from venture.test.config import get_ripl
from venture.test.stats import reportKnownDiscrete
from venture.test.stats import statisticalTest

@statisticalTest
def testESRRefAbsorb1():
  """
  This test ensures that an ESRRefOutputPSP does not absorb when its RequestPSP
  might change.
  """
  ripl = get_ripl()
  ripl.predict("(branch (flip 0.7) 1 0)",label="pid")
  predictions = collectSamples(ripl,"pid")
  ans = [(1, .7), (0, .3)]
  return reportKnownDiscrete(ans, predictions)
