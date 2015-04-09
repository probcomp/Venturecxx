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

from scipy import stats

from venture.test.config import in_backend
from venture.test.stats import statisticalTest, reportSameContinuous, reportSameDiscrete

@in_backend("none")
@statisticalTest
def testTwoSampleKS():
  data1 = stats.norm.rvs(size=100, loc=0., scale=1)
  data2 = stats.norm.rvs(size=100, loc=0., scale=1)
  return reportSameContinuous(data1, data2)

@in_backend("none")
def testTwoSampleChi2():
  data1 = range(5) * 5
  data2 = sorted(data1)
  assert reportSameDiscrete(data1, data2).pval == 1
