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

from scipy.stats import laplace

from venture.test.config import collectSamples, broken_in
from venture.test.config import get_ripl
from venture.test.stats import reportKnownContinuous
from venture.test.stats import statisticalTest

@statisticalTest
@broken_in('puma', "Laplace distribution not implemented in Puma")
def testLaplace1():
  "Test that laplace distribution does what it should"
  ripl = get_ripl()
  # samples
  ripl.assume("a","(laplace -3 2)", label="pid")
  observed = collectSamples(ripl,"pid")
  # true CDF
  laplace_cdf = lambda x: laplace.cdf(x, -3, 2)
  return reportKnownContinuous(laplace_cdf, observed)
