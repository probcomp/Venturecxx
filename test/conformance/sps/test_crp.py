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

from nose.tools import eq_, assert_almost_equal
from venture.test.config import get_ripl, on_inf_prim, collectSamples
from venture.test.stats import statisticalTest, reportKnownDiscrete

# TODO AXCH why is this a test? Why shouldn't it be legal to start at 0?
@on_inf_prim("none")
def testCRPSmoke():
  eq_(get_ripl().predict("((make_crp 1.0))"), 1)
  eq_(get_ripl().predict("((make_crp 1.0 .2))"), 1)

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

def testLogDensityOfCounts():
  """Ensures that the logDensityOfCounts of the CRP (represented by the
  global_log_likelihood) is equal to the sum of the predictive logDensity(table)
  returned by the sequnce of obesrvations.
  """
  for sampler in ["(make_crp a)", "(make_crp a d)"]:
    ripl = get_ripl()
    ripl.assume("a", "(uniform_continuous 0 1)")
    ripl.assume("d", "(uniform_continuous 0 1)")
    ripl.assume("f", sampler)

    ripl.force("a", ".5")
    [x1] = ripl.observe("(f)", "atom<1>")
    [x2] = ripl.observe("(f)", "atom<2>")
    [x3] = ripl.observe("(f)", "atom<3>")
    [x4] = ripl.observe("(f)", "atom<4>")
    [ckpt1] = ripl.infer('global_log_likelihood')
    assert_almost_equal(ckpt1, x1+x2+x3+x4)

    ripl.force("a", ".1")
    [ckpt2] = ripl.infer('global_log_likelihood')
    [y1] = ripl.observe("(f)", "atom<1>")
    [y2] = ripl.observe("(f)", "atom<2>")
    [y3] = ripl.observe("(f)", "atom<3>")
    [y4] = ripl.observe("(f)", "atom<4>")
    [ckpt3] = ripl.infer('global_log_likelihood')
    assert_almost_equal(ckpt3-ckpt2, y1+y2+y3+y4)
