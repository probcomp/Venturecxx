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

import scipy.stats as stats
from venture.test.config import get_ripl, collectSamples, skipWhenRejectionSampling
from venture.test.stats import statisticalTest, reportKnownContinuous

@skipWhenRejectionSampling("Rejection sampling doesn't work when resimulations of unknown code are observed")
@statisticalTest
def testBranch1():
  ripl = get_ripl()

  ripl.assume("p","(uniform_continuous 0.0 1.0)",label="pid")
  ripl.assume("x","""
(branch (bernoulli p)
  (quote (normal 10.0 1.0))
  (quote (normal 0.0 1.0)))
""")
  ripl.observe("x",11.0)
  predictions = collectSamples(ripl,"pid")
  cdf = stats.beta(2,1).cdf # The observation nearly guarantees the first branch is taken
  return reportKnownContinuous(cdf, predictions, "approximately beta(2,1)")
