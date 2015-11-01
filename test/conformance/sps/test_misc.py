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

import math
from nose.tools import eq_

from venture.test.config import get_ripl, on_inf_prim, broken_in

@on_inf_prim("none")
def testAssessSmoke():
  eq_(math.log(0.5), get_ripl().infer("(return (assess true bernoulli 0.5))"))

@broken_in("puma", "Can't use Lite assess in Puma because can't package "
           "Puma SP argument to it")
def testAssessAuxSmoke():
  r = get_ripl()
  r.assume("coin", "(make_beta_bernoulli 1 1)")
  eq_(math.log(0.5), r.sample("(assess true coin)"))
  r.observe("(coin)", True)
  eq_(math.log(float(2)/3), r.sample("(assess true coin)"))
