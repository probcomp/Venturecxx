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

from __future__ import division

import numpy as np

from venture.lite.utils import T_logistic
from venture.lite.utils import d_log_logistic
from venture.lite.utils import log_logistic
from venture.lite.utils import logistic

def relerr(expected, actual):
  if expected == 0:
    return 0 if actual == 0 else 1
  else:
    return abs((actual - expected)/expected)

def check(x, Lx, dLx, logLx, dlogLx):
  assert relerr(Lx, logistic(x)) < 1e-15
  if Lx < 1:
    assert relerr(1 - Lx, logistic(-x)) < 1e-15
  else:
    assert logistic(-x) < 1e-300
  assert relerr(Lx, T_logistic(x)[0]) < 1e-15
  if Lx < 1:
    assert relerr(1 - Lx, T_logistic(-x)[0]) < 1e-15
  else:
    assert T_logistic(-x)[0] < 1e-300
  assert relerr(dLx, T_logistic(x)[1]) < 1e-15
  assert relerr(dLx, T_logistic(-x)[1]) < 1e-15
  assert relerr(logLx, log_logistic(x)) < 1e-15
  if Lx < 1:
    assert relerr(np.log1p(-Lx), log_logistic(-x)) < 1e-15
  assert relerr(dlogLx, d_log_logistic(x)) < 1e-15
  if dlogLx < 1:
    assert relerr(1 - dlogLx, d_log_logistic(-x)) < 1e-15
  else:
    assert d_log_logistic(-x) < 1e-300

def testLogistic():
  check(0, 1/2, 1/4, np.log(1/2), 1/2)
  check(-1, 0.2689414213699951, 0.19661193324148185, -1.3132616875182228,
    0.7310585786300049)
  check(+1, 0.7310585786300049, 0.19661193324148185, -0.3132616875182228,
    0.2689414213699951)
  check(+710, 1, 4.4762862256751298e-309, -4.4762862256751298e-309,
    4.4762862256751298e-309)
  check(-710, 4.4762862256751298e-309, 4.4762862256751298e-309, -710, 1)
  check(+1000, 1, 0, 0, 0)
  check(-1000, 0, 0, -1000, 1)
  check(1e308, 1, 0, 0, 0)
  check(-1e308, 0, 0, -1e308, 1)

  inf = float('inf')
  assert logistic(inf) == 1
  assert logistic(-inf) == 0
  assert T_logistic(inf) == (1, 0)
  assert T_logistic(-inf) == (0, 0)
  assert log_logistic(inf) == 0
  assert log_logistic(-inf) == -inf
  assert d_log_logistic(inf) == 0
  assert d_log_logistic(-inf) == 1

  nan = float('nan')
  assert np.isnan(logistic(nan))
  assert np.isnan(T_logistic(nan)[0])
  assert np.isnan(T_logistic(nan)[1])
  assert np.isnan(log_logistic(nan))
  assert np.isnan(d_log_logistic(nan))
