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

from nose.tools import eq_

from venture.test.config import collectSamples
from venture.test.config import get_ripl
from venture.test.config import on_inf_prim
from venture.test.config import skipWhenRejectionSampling
from venture.test.stats import reportKnownGaussian
from venture.test.stats import statisticalTest
import venture.value.dicts as v

@on_inf_prim("none")
def testMVGaussSmoke():
  eq_(get_ripl().predict("(is_vector (multivariate_normal (vector 1 2) (matrix (array (array 3 4) (array 4 6)))))"), True)

@statisticalTest
def testMVGaussPrior():
  """Confirm that projecting a multivariate Gaussian to one dimension
  results in a univariate Gaussian."""

  ripl = get_ripl()
  ripl.assume("vec", "(multivariate_normal (vector 1 2) (matrix (array (array 1 0.5) (array 0.5 1))))")
  ripl.predict("(lookup vec 0)",label="prediction")

  predictions = collectSamples(ripl, "prediction")
  return reportKnownGaussian(1, 1, predictions)

@statisticalTest
def testMVN1a():
  "Check that MVN recovers normal correctly"
  ripl = get_ripl()

  ripl.assume("mu","(vector 10)")
  ripl.assume("sigma","(matrix (array (array 1.0)))")
  ripl.assume("x","(multivariate_normal mu sigma)")
  ripl.predict("(lookup x 0)",label="pid")

  predictions = collectSamples(ripl,"pid")
  return reportKnownGaussian(10, 1, predictions)

@statisticalTest
def testMVN1b():
  "Check that MVN recovers normal with observe correctly"
  ripl = get_ripl()

  ripl.assume("mu","(vector 10)")
  ripl.assume("sigma","(matrix (array (array 1.0)))")
  ripl.assume("x","(multivariate_normal mu sigma)")
  ripl.observe("(normal (lookup x 0) 1.0)","14")
  ripl.predict("(lookup x 0)",label="pid")

  predictions = collectSamples(ripl,"pid",infer="mixes_slowly")
  return reportKnownGaussian(12, math.sqrt(0.5), predictions)

@statisticalTest
def testMVN2a():
  "Check that MVN runs in 2 dimensions"
  ripl = get_ripl()

  ripl.assume("mu","(vector 100 10)")
  ripl.assume("sigma","(matrix (array (array 1.0 0.2) (array 0.2 1.0)))")
  ripl.assume("x","(multivariate_normal mu sigma)")
  ripl.predict("(lookup x 1)",label="pid")

  predictions = collectSamples(ripl,"pid")
  return reportKnownGaussian(10, 1, predictions)

@statisticalTest
def testMVN2b():
  "Check that MVN runs in 2 dimensions with observe"
  ripl = get_ripl()

  ripl.assume("mu","(vector 100 10)")
  ripl.assume("sigma","(matrix (array (array 1.0 0.2) (array 0.2 1.0)))")
  ripl.assume("x","(multivariate_normal mu sigma)")
  ripl.observe("(normal (lookup x 1) 1.0)","14")
  ripl.predict("(lookup x 1)",label="pid")

  predictions = collectSamples(ripl,"pid")
  return reportKnownGaussian(12, math.sqrt(0.5), predictions)

@skipWhenRejectionSampling("MVN has no log density bound")
@statisticalTest
def testMVN3():
  "Check that MVN is observable"
  ripl = get_ripl()

  ripl.assume("mu","(vector 0 0)")
  ripl.assume("sigma","(matrix (array (array 1.0 0.0) (array 0.0 1.0)))")
  ripl.assume("x","(multivariate_normal mu sigma)")
  ripl.assume("y","(multivariate_normal x sigma)")
  ripl.observe("y",v.vector([2, 2]))
  ripl.predict("(lookup x 0)",label="pid")

  predictions = collectSamples(ripl,"pid")
  return reportKnownGaussian(1, math.sqrt(0.5), predictions)
