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

import math

from venture.test.stats import statisticalTest
from venture.test.stats import reportKnownGaussian
from venture.test.config import get_ripl, collectSamples

@statisticalTest
def testNormal1():
  ripl = get_ripl()
  ripl.predict("(normal 0 1)", label="pid")
  predictions = collectSamples(ripl,"pid")
  return reportKnownGaussian(0, 1, predictions)

@statisticalTest
def testNormal2():
  ripl = get_ripl()
  ripl.assume("x","(normal 0 1)")
  ripl.predict("(normal x 1)")
  predictions = collectSamples(ripl,"x")
  return reportKnownGaussian(0, 1, predictions)

@statisticalTest
def testNormal3():
  ripl = get_ripl()
  ripl.assume("f","(lambda (mu) (normal mu 1))")
  ripl.predict("(f (normal 0 1))", label="pid")
  predictions = collectSamples(ripl,"pid")
  return reportKnownGaussian(0, math.sqrt(2), predictions)

@statisticalTest
def testNormal4():
  ripl = get_ripl()
  ripl.assume("f","(lambda (mu) (normal mu 1))")
  ripl.assume("g","(lambda (x y z) ((lambda () f)))")
  ripl.predict("((g (f (normal 0 1)) (f 5) (f (f 1))) 5)", label="pid")
  predictions = collectSamples(ripl,"pid")
  return reportKnownGaussian(5, 1, predictions)
