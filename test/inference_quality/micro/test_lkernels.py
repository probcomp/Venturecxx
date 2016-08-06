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

import math

from venture.test.config import collectSamples
from venture.test.config import default_num_samples
from venture.test.config import get_ripl
from venture.test.config import on_inf_prim
from venture.test.stats import reportKnownGaussian
from venture.test.stats import statisticalTest

@on_inf_prim("block mh")
@statisticalTest
def testMVNormalRandomWalkSoundness(seed):
  # This exercises the subtlety involving block proposals and delta
  # kernels described in the "joint-delta-kernels" footnote in
  # doc/on-latents.md.
  r = get_ripl(seed=seed)
  r.assume("mean", "(multivariate_normal (array 0) (id_matrix 1))")
  r.assume("y", "(multivariate_normal mean (id_matrix 1))")
  predictions = [c[0] for c in
                 collectSamples(r, "y", infer="(mh default all 50)",
                                num_samples=default_num_samples(10))]
  return reportKnownGaussian(0, math.sqrt(2), predictions)
