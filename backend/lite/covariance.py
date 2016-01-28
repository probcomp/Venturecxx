# -*- coding: utf-8 -*-

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

import numpy as np
import scipy.spatial.distance

# Trivial covariance kernel

def const(c):
  def k(x_1, x_2):
    return c*np.ones((len(x_1), len(x_2)))
  return k

# Isotropic covariance kernels

def isotropic(f):
  """Isotropic kernel: k(x_1, x_2) = f(||x_1 - x_2||^2)."""
  def k(x_1, x_2):
    x_1 = x_1.reshape(len(x_1), -1)
    x_2 = x_2.reshape(len(x_2), -1)
    return f(scipy.spatial.distance.cdist(x_1, x_2, 'sqeuclidean'))
  return k

def delta(tolerance):
  """Delta kernel: 1, if r^2 is at most tolerance; else 0."""
  def f(r2):
    return 1.*(r2 < tolerance)
  return isotropic(f)

def _se(r2, l2):
  return np.exp(-0.5 * r2 / l2)

def se(l2):
  """Squared-exponential kernel: e^(-r^2 / (2 l^2))"""
  return isotropic(lambda r2: _se(r2, l2))

def periodic(l2, period):
  """Periodic kernel: e^(-(2 sin(2pi r / p))^2 / (2 l^2))"""
  sin = np.sin
  pi = np.pi
  sqrt = np.sqrt
  def f(r2):
    r = 2.*sin(2.*pi*sqrt(r2)/period)
    return _se(r**2, l2)
  return isotropic(f)

def rq(l2, alpha):
  """Rational quadratic kernel: (1 + r^2/(2 alpha l^2))^-alpha"""
  def f(r2):
    return np.power(1. + r2/(2 * alpha * l2), -alpha)
  return isotropic(f)

def matern(l2, df):
  """Matérn kernel with squared length-scale l2 and nu = df/2."""
  import scipy.special
  nu = df/2.
  c = np.exp((1. - nu)*np.log(2.) - scipy.special.gammaln(nu))
  def f(r2):
    q = np.sqrt(df*r2/l2)
    return c * np.power(q, nu) * scipy.special.kv(nu, q)
  return isotropic(f)

def matern_32(l2):
  """Matérn kernel specialized with three degrees of freedom."""
  def f(r2):
    q = np.sqrt(3.*r2/l2)
    return (1. + q)*np.exp(-q)
  return isotropic(f)

def matern_52(l2):
  """Matérn kernel specialized with five degrees of freedom."""
  def f(r2):
    q2 = 5.*r2/l2
    q = np.sqrt(q2)
    return (1. + q + q2/3.)*np.exp(-q)
  return isotropic(f)

def linear(o):
  """Linear covariance kernel: k(x_1, x_2) = (x_1 - o) (x_2 - o)."""
  def k(x_1, x_2):
    return np.outer(x_1 - o, x_2 - o)
  return k

# Composite covariance kernels

def noise(n2, k):
  """Kernel k with constant additive squared noise n2."""
  return lambda x_1, x_2: n2 + k(x_1, x_2)

def scale(s2, k):
  """Kernel k scaled by squared output factor s2."""
  return lambda x_1, x_2: s2 * k(x_1, x_2)

def sum(k_a, k_b):
  """Sum of kernels k_a and k_b."""
  return lambda x_1, x_2: k_a(x_1, x_2) + k_b(x_1, x_2)

def product(k_a, k_b):
  """Product of kernels k_a and k_b."""
  return lambda x_1, x_2: k_a(x_1, x_2) * k_b(x_1, x_2)
