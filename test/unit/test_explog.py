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

import math

from nose.tools import assert_raises

from venture.lite.utils import careful_exp
from venture.lite.utils import extendedLog
from venture.lite.utils import extendedLog1p
from venture.lite.utils import logsumexp

def relerr(expected, actual):
  if expected == 0:
    return 0 if actual == 0 else 1
  else:
    return abs((actual - expected)/expected)

def test_log():
  inf = float('inf')
  nan = float('nan')
  assert extendedLog(0) == -inf
  assert extendedLog(1) == 0
  assert relerr(1, extendedLog(2.718281828)) < 1e-8
  assert extendedLog(+inf) == +inf
  assert math.isnan(extendedLog(nan))

def test_log1p():
  inf = float('inf')
  nan = float('nan')
  assert extendedLog1p(-1) == -inf
  assert extendedLog1p(0) == 0
  assert relerr(1, extendedLog1p(1.718281828)) < 1e-8
  assert extendedLog1p(+inf) == +inf
  assert relerr(1e-20, extendedLog1p(1e-20)) < 1e-16
  assert math.isnan(extendedLog1p(nan))

def test_exp():
  inf = float('inf')
  nan = float('nan')
  assert careful_exp(-inf) == 0
  assert careful_exp(0) == 1
  assert relerr(2.718281828, careful_exp(1)) < 1e-8
  assert careful_exp(+inf) == +inf
  assert math.isnan(careful_exp(nan))

def test_logsumexp():
  inf = float('inf')
  nan = float('nan')
  assert_raises(OverflowError,
    lambda: math.log(sum(map(math.exp, range(1000)))))
  assert relerr(999.4586751453871, logsumexp(range(1000))) < 1e-15
  assert logsumexp([]) == -inf
  assert logsumexp([-1000.]) == -1000.
  assert logsumexp([-1000., -1000.]) == -1000. + math.log(2.)
  assert relerr(math.log(2.), logsumexp([0., 0.])) < 1e-15
  assert logsumexp([-inf, 1]) == 1
  assert logsumexp([-inf, -inf]) == -inf
  assert logsumexp([+inf, +inf]) == +inf
  assert math.isnan(logsumexp([-inf, +inf]))
  assert math.isnan(logsumexp([nan, inf]))
  assert math.isnan(logsumexp([nan, -3]))
