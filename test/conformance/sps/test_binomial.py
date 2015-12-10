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

from nose.tools import assert_almost_equal
import scipy.stats

from venture.test.config import broken_in
from venture.test.config import collectSamples
from venture.test.config import default_num_transitions_per_sample
from venture.test.config import get_ripl
from venture.test.config import on_inf_prim
from venture.test.stats import reportKnownDiscrete
from venture.test.stats import statisticalTest

@statisticalTest
def testBinomial1():
  "A simple test that checks the interface of binomial and its simulate method"
  ripl = get_ripl()

  p = 0.3
  n = 4
  ripl.assume("p","(if (flip) %f %f)" % (p,p))
  ripl.predict("(binomial %d p)" % n,label="pid")

  predictions = collectSamples(ripl,"pid")
  ans = [(x,scipy.stats.binom.pmf(x,n,p)) for x in range(n+1)]
  assert_almost_equal(sum([xx[1] for xx in ans]),1)
  return reportKnownDiscrete(ans, predictions)

@statisticalTest
def testBinomial2():
  "A simple test that checks the binomial logdensity"
  ripl = get_ripl()

  b = 0.7
  p1 = 0.3
  p2 = 0.4
  n = 4
  ripl.assume("p","(if (flip %f) %f %f)" % (b,p1,p2))
  ripl.predict("(binomial %d p)" % n,label="pid")

  predictions = collectSamples(ripl,"pid")
  ans = [(x,b * scipy.stats.binom.pmf(x,n,p1) + (1 - b) * scipy.stats.binom.pmf(x,n,p2)) for x in range(n+1)]
  assert_almost_equal(sum([xx[1] for xx in ans]),1)
  return reportKnownDiscrete(ans, predictions)

@statisticalTest
@broken_in("puma", "Puma is missing an enumerate method here")
@on_inf_prim("gibbs") # Also MH, but really testing gibbs
def testBinomial3():
  "A simple test that checks the binomial enumerate method"
  ripl = get_ripl()

  b = 0.7
  p1 = 0.3
  p2 = 0.4
  n = 4
  ripl.assume("p","(tag 0 1 (if (flip %f) %f %f))" % (b,p1,p2))
  ripl.predict("(tag 0 0 (binomial %d p))" % n,label="pid")

  predictions = collectSamples(ripl,"pid",infer="(repeat %s (do (mh 0 1 1) (gibbs 0 0 1)))" % default_num_transitions_per_sample())

  ans = [(x,b * scipy.stats.binom.pmf(x,n,p1) + (1 - b) * scipy.stats.binom.pmf(x,n,p2)) for x in range(n+1)]
  assert_almost_equal(sum([xx[1] for xx in ans]),1)
  return reportKnownDiscrete(ans, predictions)
