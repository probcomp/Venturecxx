# Copyright (c) 2016 MIT Probabilistic Computing Project.
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

from venture.test.config import broken_in
from venture.test.config import collectSamples
from venture.test.config import get_ripl
from venture.test.config import on_inf_prim
from venture.test.stats import reportKnownDiscrete
from venture.test.stats import statisticalTest

@statisticalTest
@broken_in("puma", "Puma does not support rejection sampling")
@on_inf_prim("rejection")
def testUserDensityBound(seed):
  r = get_ripl(seed=seed)
  r.set_mode("venture_script")
  r.execute_program("""
  assume f = (small) ~> {
  if (small) {
    uniform_continuous(0, 1)
  } else {
    uniform_continuous(0, 10)
  }};
  assume small = flip(0.5);
  observe f(small) = 0.2;
""")

  predictions = collectSamples(r, "small", infer="rejection(default, all, 0, 1)")
  return reportKnownDiscrete([(True, 10), (False, 1)], predictions)
