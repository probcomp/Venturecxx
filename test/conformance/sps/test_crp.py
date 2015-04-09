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

from nose.tools import eq_
from venture.test.config import get_ripl, on_inf_prim, collectSamples
from venture.test.stats import statisticalTest, reportKnownDiscrete

# TODO AXCH why is this a test? Why shouldn't it be legal to start at 0?
@on_inf_prim("none")
def testCRPSmoke():
  eq_(get_ripl().predict("((make_crp 1.0))"), 1)

def replaceWithDefault(items, known, default):
  "Replace all irrelevant items with a default."
  ret = []
  for item in items:
    if item in known:
      ret.append(item)
    else:
      ret.append(default)
  return ret

@statisticalTest
def testCRP1():
  ripl = get_ripl()
  ripl.assume("f", "(make_crp 1)")
  ripl.observe("(f)", "atom<1>")
  ripl.observe("(f)", "atom<1>")
  ripl.observe("(f)", "atom<2>")
  ripl.predict("(f)", label="pid")

  predictions = collectSamples(ripl, "pid")
  ans = [(1, 0.5), (2, 0.25), ("other", 0.25)]
  return reportKnownDiscrete(ans, replaceWithDefault(predictions, [1, 2], "other"))

def testCRPCounter():
  "Make sure that the next table counter doesn't get stuck on an existing value."
  for i in range(1, 6):
    yield checkCRPCounter, i

@statisticalTest
def checkCRPCounter(n):
  ripl = get_ripl()
  ripl.assume("f", "(make_crp 1)")
  ripl.observe("(f)", "atom<%d>" % n)
  ripl.predict("(f)", label="pid")

  predictions = collectSamples(ripl, "pid")
  ans = [(n, 0.5), ("other", 0.5)]
  return reportKnownDiscrete(ans, replaceWithDefault(predictions, [n], "other"))
