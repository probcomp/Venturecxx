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

from math import isinf

import numpy as np

from venture.lite.utils import T_logistic
from venture.lite.utils import d_log_logistic
from venture.lite.utils import d_logistic
from venture.lite.utils import d_logit_exp
from venture.lite.utils import exp
from venture.lite.utils import log_d_logistic
from venture.lite.utils import log_logistic
from venture.lite.utils import logistic
from venture.lite.utils import logit
from venture.lite.utils import logit_exp

def relerr(expected, actual):
  if expected == 0:
    return 0 if actual == 0 else 1
  else:
    return abs((actual - expected)/expected)

def check(x, Lx, dLx, logLx, dlogLx, logdLx):
  assert relerr(Lx, logistic(x)) < 1e-15
  if Lx not in (0, 1):
    assert relerr(x, logit(Lx)) < 1e-15
  if Lx < 1:
    assert relerr(1 - Lx, logistic(-x)) < 1e-15
    if abs(x) < 709:
      assert relerr(-x, logit(1 - Lx)) < 1e-15
  else:
    assert logistic(-x) < 1e-300
  assert relerr(Lx, T_logistic(x)[0]) < 1e-15
  if Lx < 1:
    assert relerr(1 - Lx, T_logistic(-x)[0]) < 1e-15
  else:
    assert T_logistic(-x)[0] < 1e-300
  assert relerr(dLx, T_logistic(x)[1]) < 1e-15
  assert relerr(dLx, d_logistic(x)) < 1e-15
  assert relerr(dLx, exp(log_d_logistic(x))) < 1e-15
  assert relerr(logdLx, log_d_logistic(x)) < 1e-15
  assert relerr(dLx, T_logistic(-x)[1]) < 1e-15
  assert relerr(dLx, d_logistic(-x)) < 1e-15
  assert relerr(dLx, exp(log_d_logistic(x))) < 1e-15
  assert relerr(logdLx, log_d_logistic(x)) < 1e-15
  assert relerr(logLx, log_logistic(x)) < 1e-15
  if x <= 709:
    assert relerr(x, logit_exp(logLx)) < 1e-15
  if Lx < 1:
    assert relerr(np.log1p(-Lx), log_logistic(-x)) < 1e-15
  assert relerr(dlogLx, d_log_logistic(x)) < 1e-15
  if 710 <= x:
    assert isinf(d_logit_exp(logLx))
  if 1e-308 < dlogLx:
    assert relerr(1/dlogLx, d_logit_exp(logLx)) < 1e-15
  if dlogLx < 1:
    assert relerr(1 - dlogLx, d_log_logistic(-x)) < 1e-15
  else:
    assert d_log_logistic(-x) < 1e-300

def testLogistic():
  check(0,
    Lx=1/2,
    dLx=1/4,
    logLx=np.log(1/2),
    dlogLx=1/2,
    logdLx=np.log(1/4),
  )
  check(-1,
    Lx=0.2689414213699951,
    dLx=0.19661193324148185,
    logLx=-1.3132616875182228,
    dlogLx=0.7310585786300049,
    logdLx=-1.6265233750364456,
  )
  check(+1,
    Lx=0.7310585786300049,
    dLx=0.19661193324148185,
    logLx=-0.3132616875182228,
    dlogLx=0.2689414213699951,
    logdLx=-1.6265233750364456,
  )
  check(+710,
    Lx=1,
    dLx=4.4762862256751298e-309,
    logLx=-4.4762862256751298e-309,
    dlogLx=4.4762862256751298e-309,
    logdLx=-710,
  )
  check(-710,
    Lx=4.4762862256751298e-309,
    dLx=4.4762862256751298e-309,
    logLx=-710,
    dlogLx=1,
    logdLx=-710,
  )
  check(+1000,
    Lx=1,
    dLx=0,
    logLx=0,
    dlogLx=0,
    logdLx=-1000,
  )
  check(-1000,
    Lx=0,
    dLx=0,
    logLx=-1000,
    dlogLx=1,
    logdLx=-1000,
  )
  check(1e308,
    Lx=1,
    dLx=0,
    logLx=0,
    dlogLx=0,
    logdLx=-1e308,
  )
  check(-1e308,
    Lx=0,
    dLx=0,
    logLx=-1e308,
    dlogLx=1,
    logdLx=-1e308,
  )

  inf = float('inf')
  assert logistic(inf) == 1
  assert logistic(-inf) == 0
  assert T_logistic(inf) == (1, 0)
  assert T_logistic(-inf) == (0, 0)
  assert d_logistic(inf) == 0
  assert d_logistic(-inf) == 0
  assert log_d_logistic(inf) == -inf
  assert log_d_logistic(-inf) == -inf
  assert log_logistic(inf) == 0
  assert log_logistic(-inf) == -inf
  assert d_log_logistic(inf) == 0
  assert d_log_logistic(-inf) == 1

  nan = float('nan')
  assert np.isnan(logistic(nan))
  assert np.isnan(T_logistic(nan)[0])
  assert np.isnan(T_logistic(nan)[1])
  assert np.isnan(d_logistic(nan))
  assert np.isnan(log_d_logistic(nan))
  assert np.isnan(log_logistic(nan))
  assert np.isnan(d_log_logistic(nan))

def test_vector_logistic():
  inputs    = np.array([-1e308, -1000, -710, -1, 0, 1, 710, 1000, 1e308])
  logistics = np.array([0, 0, 4.4762862256751298e-309, 0.2689414213699951, 0.5, 0.7310585786300049, 1, 1, 1])
  assert np.allclose(logistics, logistic(inputs))
  assert np.allclose(logistics, T_logistic(inputs)[0])
