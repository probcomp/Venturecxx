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

from venture.test.config import collectSamples
from venture.test.config import get_ripl
from venture.test.config import on_inf_prim
from venture.test.stats import reportKnownContinuous
from venture.test.stats import statisticalTest

@on_inf_prim("none")
def testEq():
  r = get_ripl()
  assert r.predict("(eq 1 1)")
  assert not r.predict("(eq 1 2)")
  assert not r.predict("(neq 1 1)")
  assert r.predict("(neq 1 2)")
  r.set_mode("venture_script")
  assert r.predict("1 == 1")
  assert r.predict("eq(1, 1)")
  assert not r.predict("1 == 2")
  assert not r.predict("eq(1, 2)")
  assert not r.predict("1 != 1")
  assert not r.predict("neq(1, 1)")
  assert r.predict("1 != 2")
  assert r.predict("neq(1, 2)")

@on_inf_prim("none")
def testCompare():
  assert get_ripl().predict("(<= 1 1)")
  assert get_ripl().predict("(< 1 2)")
  assert not get_ripl().predict("(> 1 2)")
  assert not get_ripl().predict("(>= 1 2)")

@on_inf_prim("none")
def testAnyAll():
  # list argument
  assert get_ripl().predict("(any_p (list True False True))")
  assert not get_ripl().predict("(any_p (list False False False))")
  assert get_ripl().predict("(all_p (list True True True))")
  assert not get_ripl().predict("(all_p (list True False False))")
  # array argument
  assert get_ripl().predict("(any_p (array True False True))")
  assert not get_ripl().predict("(any_p (array False False False))")
  assert get_ripl().predict("(all_p (array True True True))")
  assert not get_ripl().predict("(all_p (array True False False))")

@on_inf_prim("none")
def testRecordSmoke():
  assert not get_ripl().evaluate("(eq 1 (return 1))")

def testBasicCDFs():
  yield checkCDF, "(normal 1 1)", scipy.stats.norm(loc=1, scale=1).cdf
  yield checkCDF, "(uniform_continuous 0 1)", lambda x: x
  yield checkCDF, "(beta 1 1)", scipy.stats.beta(1, 1).cdf
  yield checkCDF, "(gamma 1 2)", scipy.stats.gamma(1, scale=1/2.0).cdf
  yield checkCDF, "(student_t 1)", scipy.stats.t(1).cdf
  yield checkCDF, "(inv_gamma 1 2)", scipy.stats.invgamma(1, scale=2.0).cdf

@statisticalTest
def checkCDF(expr, cdf, seed):
  ripl = get_ripl(seed=seed)
  ripl.predict(expr, label = "pid")
  predictions = collectSamples(ripl, "pid")
  return reportKnownContinuous(cdf, predictions, expr)
