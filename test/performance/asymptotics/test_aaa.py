# Copyright (c) 2015 MIT Probabilistic Computing Project.
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

from nose import SkipTest

from venture.test.config import get_ripl
import venture.test.timing as timing

def testBernoulli():
  yield checkBernoulli, "(make_suff_stat_bernoulli (uniform_continuous 0 1))"
  yield checkBernoulli, "(make_uc_beta_bernoulli 1 1)"
  yield checkBernoulli, "(make_beta_bernoulli (uniform_discrete 1 4) 1)"

def checkBernoulli(maker):
  raise SkipTest("AAA does not actually make proposals constant-time, for some reason.")
  def test_fun(num_obs):
    ripl = get_ripl()
    ripl.assume("coin", maker)
    for _ in range(num_obs):
      ripl.observe("(coin)", True)
    return lambda: ripl.infer("(mh default one 10)")
  timing.assertConstantTime(test_fun)
