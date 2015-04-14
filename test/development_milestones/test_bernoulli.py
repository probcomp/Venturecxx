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

import math
import scipy.stats as stats
from nose import SkipTest

from venture.test.stats import statisticalTest, reportKnownContinuous, reportKnownMeanVariance, reportKnownDiscrete
from venture.test.config import get_ripl, collectSamples, collect_iid_samples

@statisticalTest
def testBernoulli1():
  ripl = get_ripl()
  ripl.predict("(bernoulli 0.3)")
  # ripl.assume("x2", "(bernoulli 0.4)")
  # ripl.assume("x3", "(bernoulli 0.0)")
  # ripl.assume("x4", "(bernoulli 1.0)")
  # ripl.assume("x5", "(bernoulli)")  

  predictions = collectSamples(ripl,1)
  ans = [(True, 0.3),(False, 0.7)]
  return reportKnownDiscrete(ans, predictions)

@statisticalTest
def testCategorical1():
  ripl = get_ripl()
  ripl.predict("(categorical (simplex 0.3 0.7))")
  # ripl.assume("x2", "(bernoulli 0.4)")
  # ripl.assume("x3", "(bernoulli 0.0)")
  # ripl.assume("x4", "(bernoulli 1.0)")
  # ripl.assume("x5", "(bernoulli)")  

  predictions = collectSamples(ripl,1)
  ans = [(0, 0.3),(1, 0.7)]
  return reportKnownDiscrete(ans, predictions)

@statisticalTest
def testCategorical2():
  ripl = get_ripl()
  ripl.predict("(categorical (simplex 0.3 0.7) (array true false))")
  # ripl.assume("x2", "(bernoulli 0.4)")
  # ripl.assume("x3", "(bernoulli 0.0)")
  # ripl.assume("x4", "(bernoulli 1.0)")
  # ripl.assume("x5", "(bernoulli)")  

  predictions = collectSamples(ripl,1)
  ans = [(True, 0.3),(False, 0.7)]
  return reportKnownDiscrete(ans, predictions)
