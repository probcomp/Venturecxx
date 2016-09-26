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

from venture.test.config import collectSamples
from venture.test.config import gen_broken_in
from venture.test.config import gen_on_inf_prim
from venture.test.config import get_ripl
from venture.test.stats import reportKnownGaussian
from venture.test.stats import statisticalTest

@gen_broken_in("puma", "Meanfield not implemented in Puma")
@gen_on_inf_prim("meanfield")
def testMeanFieldBasic():
  tests = (checkMeanFieldBasic1, checkMeanFieldNormalWithObserve1)
  for test in tests: yield test, "(meanfield default one 20 10)"

@statisticalTest
def checkMeanFieldBasic1(infer, seed):
  # Basic sanity test for meanfield
  ripl = get_ripl(seed=seed)
  ripl.assume("a", "(normal 10.0 1.0)",label="pid")
  predictions = collectSamples(ripl,"pid",infer=infer)
  return reportKnownGaussian(10, 1, predictions)

@statisticalTest
def checkMeanFieldNormalWithObserve1(infer, seed):
  # Checks the posterior distribution on a Gaussian given an unlikely
  # observation
  ripl = get_ripl(seed=seed)
  ripl.assume("a", "(normal 10.0 1.0)",label="pid")
  ripl.observe("(normal a 1.0)", 14.0)
  # Posterior for a is normal with mean 12, precision 2
#  ripl.predict("(normal a 1.0)")

  predictions = collectSamples(ripl,"pid",infer=infer)
  return reportKnownGaussian(12, math.sqrt(0.5), predictions)
