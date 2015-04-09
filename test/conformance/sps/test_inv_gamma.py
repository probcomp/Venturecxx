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

from venture.test.stats import statisticalTest, reportKnownContinuous
from venture.test.config import get_ripl, collectSamples
from scipy.stats import invgamma

@statisticalTest
def testInvGamma1():
  "Check that Gamma is parameterized correctly"
  ripl = get_ripl()
  # samples
  ripl.assume("a","(inv_gamma 10.0 10.0)", label="pid")
  observed = collectSamples(ripl,"pid")
  # true CDF
  inv_gamma_cdf = lambda x: invgamma.cdf(x, a = 10, scale = 10)
  return reportKnownContinuous(inv_gamma_cdf, observed)
