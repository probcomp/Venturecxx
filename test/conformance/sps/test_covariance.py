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

import copy

import numpy as np

from numpy.testing import assert_allclose

import venture.lite.covariance as cov

from venture.lite.mlens import real_lenses
from venture.test.numerical import gradient_from_lenses

# XXX Kludge to avoid VenturePartialDiffableFunction.
class DKernel(object):
  def __init__(self, dk_dtheta):
    self._dk_dtheta = dk_dtheta
  def df_theta(self, X, Y):
    return self._dk_dtheta(X, Y)

class Box(object):
  def __init__(self, content):
    self._content = content
  def get(self):
    return self._content
  def set(self, content):
    self._content = content

class ListLens(object):
  def __init__(self, l, i):
    assert isinstance(l, list)
    assert isinstance(i, int)
    self._l = l
    self._i = i
  def get(self):
    return self._l[self._i]
  def set(self, x):
    self._l[self._i] = x

def list_lenses(theta):
  assert isinstance(theta, list)
  queue = [theta]
  lenses = []
  for l in queue:
    for i, x in enumerate(l):
      if isinstance(x, list):
        queue.append(x)
      elif isinstance(x, (int, float)):
        lenses.append(ListLens(l, i))
      else:
        # covariance kernel
        pass
  return lenses

def check_ddtheta(f, df_dtheta, theta):
  lenses = list_lenses(theta)
  analytical = [dk_i.tolist() for dk_i in df_dtheta()]
  analytical_values = [lens.get() for lens in list_lenses(analytical)]
  assert np.all(np.isfinite(analytical_values)), '%r' % (analytical_values,)
  numerical_values = gradient_from_lenses(f, lenses, step0=0.0001)
  assert np.all(np.isfinite(numerical_values)), '%r' % (numerical_values,)
  assert_allclose(numerical_values, analytical_values)

def test_ddtheta_const():
  for x in [-1, 0, 1]:
    X = np.array([x])
    for y in [-1, 0, 1]:
      Y = np.array([y])
      for c in [-1, 0, 1]:
        theta = [c]
        def f():
          return cov.const(theta[0])(X, Y)[0][0]
        def df_dtheta():
          k, dk = cov.ddtheta_const(theta[0])(X, Y)
          assert all(np.all(dki != 0) for dki in dk)
          return dk
        check_ddtheta(f, df_dtheta, theta)

def test_ddtheta_se():
  for x in [-1, 0, 1]:
    X = np.array([x])
    for y in [-1, 0, 1]:
      Y = np.array([y])
      for l2 in [.01, 1, 10, 100]:
        theta = [l2]
        def f():
          return cov.se(theta[0])(X, Y)[0][0]
        def df_dtheta():
          k, dk = cov.ddtheta_se(theta[0])(X, Y)
          if x == y:
            assert all(np.all(dki == 0) for dki in dk)
          else:
            assert all(np.all(dki != 0) for dki in dk)
          return dk
        check_ddtheta(f, df_dtheta, theta)

def test_ddtheta_se_scaled():
  for x in [-1, 0, 1]:
    X = np.array([x])
    for y in [-1, 0, 1]:
      Y = np.array([y])
      for s2 in [.1, 1, 10, 100]:
        for l2 in [.1, 1, 10]:
          theta = [s2, l2]
          def f():
            return cov.scale(theta[0], cov.se(theta[1]))(X, Y)[0][0]
          def df_dtheta():
            K = DKernel(cov.ddtheta_se(theta[1]))
            k, dk = cov.ddtheta_scale(theta[0], K)(X, Y)
            assert s2*dk[0] == k, 's2*dk[0]=%r k=%r' % (s2*dk[0], k)
            if x == y:
              assert all(np.all(dki == 0) for dki in dk[1:]), 'dk=%r' % (dk,)
            else:
              assert all(np.all(dki != 0) for dki in dk[1:])
            h, dh = cov.ddtheta_se(theta[1])(X, Y)
            assert k == s2*h, 'k=%r s2*h=%r' % (k, s2*h)
            assert all(dki == s2*dhi for dki, dhi in zip(dk[1:], dh))
            return dk
          check_ddtheta(f, df_dtheta, theta)

def test_ddtheta_periodic():
  for x in [-1, 0, 1]:
    X = np.array([x])
    for y in [-1, 0, 1]:
      Y = np.array([y])
      for l2 in [.1, 1, 10]:
        for T in [2e-1*np.pi, 2*np.pi, 2e1*np.pi]:
          theta = [l2, T]
          def f():
            return cov.periodic(theta[0], theta[1])(X, Y)[0][0]
          def df_dtheta():
            k, dk = cov.ddtheta_periodic(theta[0], theta[1])(X, Y)
            if (x - y) % T == 0:
              assert all(np.all(dki == 0) for dki in dk), 'dk=%r' % (dk,)
            else:
              assert all(np.all(dki != 0) for dki in dk)
            return dk
          check_ddtheta(f, df_dtheta, theta)

def test_ddtheta_deltoid():
  for x in [-1, 0, 1]:
    X = np.array([x])
    for y in [-1, 0, 1]:
      Y = np.array([y])
      for t in [.1, 1, 10]:
        for s in [.1, 1, 10]:
          theta = [t, s]
          def f():
            return cov.deltoid(theta[0], theta[1])(X, Y)[0][0]
          def df_dtheta():
            k, dk = cov.ddtheta_deltoid(theta[0], theta[1])(X, Y)
            return dk
          check_ddtheta(f, df_dtheta, theta)

def test_ddtheta_bump():
  for x in [-1, 0, 1]:
    X = np.array([x])
    for y in [-1, 0, 1]:
      Y = np.array([y])
      for mint in [.4, 1.4, 2.4]:
        for maxt in [.6, 1.6, 2.6]:
          if maxt < mint:
            continue
          theta = [mint**2, maxt**2]
          def f():
            return cov.bump(theta[0], theta[1])(X, Y)[0][0]
          def df_dtheta():
            k, dk = cov.ddtheta_bump(theta[0], theta[1])(X, Y)
            if mint**2 < (x - y)**2 < maxt**2:
              assert all(np.all(dki != 0) for dki in dk)
            else:
              assert all(np.all(dki == 0) for dki in dk), 'dk=%r' % (dk,)
            return dk
          check_ddtheta(f, df_dtheta, theta)

def test_ddtheta_sum_se_bump():
  for x in [-1, 0, 1]:
    X = np.array([x])
    for y in [-1, 0, 1]:
      Y = np.array([y])
      for l2 in [.1, 1, 10]:
        for mint in [.4, 1.4, 2.4]:
          for maxt in [.6, 1.6, 2.6]:
            if maxt < mint:
              continue
            theta = [l2, mint, maxt]
            def f():
              K = cov.se(theta[0])
              H = cov.bump(theta[1], theta[2])
              return cov.sum(K, H)(X, Y)[0][0]
            def df_dtheta():
              K = DKernel(cov.ddtheta_se(theta[0]))
              H = DKernel(cov.ddtheta_bump(theta[1], theta[2]))
              k, dk = cov.ddtheta_sum(K, H)(X, Y)
              return dk
            check_ddtheta(f, df_dtheta, theta)
