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

from venture.test.stats import statisticalTest, reportKnownDiscrete
from venture.test.config import get_ripl, collectSamples

@statisticalTest
def testBernoulli1():
  ripl = get_ripl()
  ripl.predict("(bernoulli 0.3)", label="pid")

  predictions = collectSamples(ripl,"pid")
  ans = [(True, 0.3),(False, 0.7)]
  return reportKnownDiscrete(ans, predictions)

@statisticalTest
def testCategorical1():
  ripl = get_ripl()
  ripl.predict("(categorical (simplex 0.3 0.7))", label="pid")

  predictions = collectSamples(ripl,"pid")
  ans = [(0, 0.3),(1, 0.7)]
  return reportKnownDiscrete(ans, predictions)

@statisticalTest
def testCategorical2():
  ripl = get_ripl()
  ripl.predict("(categorical (simplex 0.3 0.7) (array true false))", label="pid")

  predictions = collectSamples(ripl,"pid")
  ans = [(True, 0.3),(False, 0.7)]
  return reportKnownDiscrete(ans, predictions)
