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

import scipy.stats
from venture.test.stats import statisticalTest, reportKnownMean, reportKnownContinuous
from venture.test.config import get_ripl, collectSamples

@statisticalTest
def testPoisson1():
  "Check that Poisson simulates and absorbs without crashing."
  ripl = get_ripl()

  ripl.assume("lambda","(gamma 1 1)",label="pid")
  #ripl.predict("(poisson lambda)")

  predictions = collectSamples(ripl,"pid")
  return reportKnownContinuous(scipy.stats.gamma(1, scale=1/1.0).cdf,predictions,"(gamma 1 1)")

@statisticalTest
def testPoisson2():
  "Check that Poisson simulates correctly."
  ripl = get_ripl()

  ripl.assume("lambda","5")
  ripl.predict("(poisson lambda)",label="pid")

  predictions = collectSamples(ripl,"pid")
  return reportKnownMean(5,predictions)
  
