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

import numpy as np

from venture import shortcuts as s
from venture.server import RiplRestServer
import venture.lite.gp as gp
import venture.lite.value as v

ripl = s.make_lite_church_prime_ripl()

program = """
  [assume mu (normal 0 5)]
  [assume mean (gp_mean_const mu)]

;  [assume a (inv_gamma 2 5)]
  [assume a 1]
;  [assume l (inv_gamma 5 50)]
;  [assume l (uniform_continuous 10 100)]
  [assume l 10]

;  [assume cov ((if (flip) gp_cov_sum gp_cov_product) (gp_cov_scale a (gp_cov_se (/ (* l l) 2.))) (gp_cov_linear (normal 0 10)))]

;  [assume noise (inv_gamma 3 1)]
  [assume noise 0.1]
  [assume noise_func (gp_cov_scale noise (gp_cov_se (/ (* .1 .1) 2.)))]

  [assume is_linear (flip)]
  [assume cov
    (gp_cov_sum noise_func
      (if is_linear
        (gp_cov_linear (normal 0 10))
        (gp_cov_scale a (gp_cov_se (/ (* l l) 2.)))))]

;  [assume cov (gp_cov_scale a (gp_cov_linear 0))]

  gp : [assume gp (make_gp mean cov)]

  [assume obs_fn (lambda (obs_id x) (gp x))]
;  [assume obs_fn (lambda (obs_id x) (normal x 1))]
"""

ripl.execute_program(program)

samples = [
  (0, 1),
  (2, 3),
  (-4, 5),
]

def array(xs):
  return v.VentureArrayUnboxed(np.array(xs), gp.xType)

xs, os = zip(*samples)

#ripl.observe(['gp', array(xs)], array(os))
ripl.infer("(incorporate)")

server = RiplRestServer(ripl)
server.run(host='127.0.0.1', port=8082)
