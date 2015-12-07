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
import scipy.stats as stats
from nose import SkipTest

from venture.test.config import broken_in
from venture.test.config import collectSamples
from venture.test.config import collect_iid_samples
from venture.test.config import default_num_transitions_per_sample
from venture.test.config import get_ripl
from venture.test.config import on_inf_prim
from venture.test.stats import reportKnownContinuous
from venture.test.stats import reportKnownDiscrete
from venture.test.stats import reportKnownGaussian
from venture.test.stats import statisticalTest

@statisticalTest
@on_inf_prim("mh")
def testBlockingExample0():
  ripl = get_ripl()
  if not collect_iid_samples():
    raise SkipTest("This test should not pass without reset.")

  ripl.assume("a", "(tag 0 0 (normal 10.0 1.0))", label="pid")
  ripl.assume("b", "(tag 1 1 (normal a 1.0))")
  ripl.observe("(normal b 1.0)", 14.0)

  # If inference only frobnicates b, then the distribution on a
  # remains the prior.
  predictions = collectSamples(ripl,"pid",infer="(mh 1 1 10)")
  return reportKnownGaussian(10, 1.0, predictions)

@on_inf_prim("mh")
def testBlockingExample1():
  ripl = get_ripl()
  ripl.assume("a", "(tag 0 0 (normal 0.0 1.0))",label="a")
  ripl.assume("b", "(tag 0 0 (normal 1.0 1.0))",label="b")
  olda = ripl.report("a")
  oldb = ripl.report("b")
  # The point of block proposals is that both things change at once.
  ripl.infer("(mh 0 0 1)")
  newa = ripl.report("a")
  newb = ripl.report("b")
  assert not olda == newa
  assert not oldb == newb

@on_inf_prim("mh")
def testBlockingExample2():
  ripl = get_ripl()
  ripl.assume("a", "(tag 0 0 (normal 0.0 1.0))", label="a")
  ripl.assume("b", "(tag 0 0 (normal 1.0 1.0))", label="b")
  ripl.assume("c", "(tag 0 1 (normal 2.0 1.0))", label="c")
  ripl.assume("d", "(tag 0 1 (normal 3.0 1.0))", label="d")
  olda = ripl.report("a")
  oldb = ripl.report("b")
  oldc = ripl.report("c")
  oldd = ripl.report("d")
  # Should change everything in one or the other block
  ripl.infer("(mh 0 one 1)")
  newa = ripl.report("a")
  newb = ripl.report("b")
  newc = ripl.report("c")
  newd = ripl.report("d")
  if olda == newa:
    assert oldb == newb
    assert not oldc == newc
    assert not oldd == newd
  else:
    assert not oldb == newb
    assert oldc == newc
    assert oldd == newd

@on_inf_prim("mh")
def testBlockingExample3():
  ripl = get_ripl()
  ripl.assume("a", "(tag 0 0 (normal 0.0 1.0))", label="a")
  ripl.assume("b", "(tag 0 1 (normal 1.0 1.0))", label="b")
  olda = ripl.report("a")
  oldb = ripl.report("b")
  # The point of block proposals is that both things change at once.
  ripl.infer("(mh 0 all 1)")
  newa = ripl.report("a")
  newb = ripl.report("b")
  assert not olda == newa
  assert not oldb == newb

@statisticalTest
@broken_in('puma', "rejection is not implemented in Puma")
@on_inf_prim("rejection")
def testBasicRejection1():
  ripl = get_ripl()
  ripl.assume("x", "(bernoulli 0.5)",label="pid")
  predictions = collectSamples(ripl, "pid", infer="(rejection default all 1)")
  ans = [(True, 0.5), (False, 0.5)]
  return reportKnownDiscrete(ans, predictions)

@statisticalTest
@broken_in('puma', "rejection is not implemented in Puma")
@on_inf_prim("rejection")
def testBasicRejection2():
  ripl = get_ripl()
  ripl.assume("p", "(uniform_continuous 0 1)")
  ripl.assume("x", "(bernoulli p)", label="pid")
  predictions = collectSamples(ripl, "pid", infer="(rejection default all 1)")
  ans = [(True, 0.5), (False, 0.5)]
  return reportKnownDiscrete(ans, predictions)

@statisticalTest
@broken_in('puma', "rejection is not implemented in Puma")
@on_inf_prim("rejection")
def testBasicRejection3():
  ripl = get_ripl()
  ripl.assume("p", "(uniform_continuous 0 1)", label="pid")
  ripl.observe("(bernoulli p)", "true")
  predictions = collectSamples(ripl, "pid", infer="(rejection default all 1)")
  cdf = stats.beta(2,1).cdf
  return reportKnownContinuous(cdf, predictions, "beta(2,1)")

@statisticalTest
@on_inf_prim("mh")
def testCycleKernel():
  """Same example as testBlockingExample0,
but a cycle kernel that covers everything should solve it"""
  ripl = get_ripl()

  ripl.assume("a", "(tag 0 0 (normal 10.0 1.0))", label="pid")
  ripl.assume("b", "(tag 1 1 (normal a 1.0))")
  ripl.observe("(normal b 1.0)", 14.0)

  infer = "(repeat %s (do (mh 0 0 1) (mh 1 1 1)))" % \
          default_num_transitions_per_sample()

  predictions = collectSamples(ripl,"pid",infer=infer)
  return reportKnownGaussian(34.0/3.0, math.sqrt(2.0/3.0), predictions)
