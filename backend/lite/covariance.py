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

r"""Gaussian process covariance kernels.

A covariance kernel on an input space A is a symmetric
positive-definite function k: A^2 ---> \R.  We currently handle A = \R
and A = \R^n for some n.  The computational representation of a
covariance kernel is a function that takes two arrays of elements of
A, X = (x_1, x_2, ..., x_m) and Y = (y_1, y_2, ..., y_l), and returns
a matrix

    [k(x_1, y_1), k(x_1, y_2), ..., k(x_1, y_l);
     k(x_2, y_1), k(x_2, y_2), ..., k(x_2, y_l);
        :              :        .          :
        :              :         .         :
     k(x_m, y_1), k(x_m, y_2), ..., k(x_m, y_l)]

of all covariances between all pairwise elements in X and Y.

For a covariance kernel k_theta parametrized by some theta = (theta^1,
theta^2, ..., theta^h), the derivative of the covariance kernel with
respect to theta is computationally represented by a function that
takes two arrays X and Y in A and returns an array of the h partial
derivatives of k_theta(X, Y) with respect to theta -- that is, returns
an array of h matrices [t_1, t_2, ..., t_h], so that t_i maps an
increment in theta^i to an increment in the covariance matrix between
X and Y:

    d k_theta(X, Y) = t_1 dtheta^1 + t_2 dtheta^2 + ... + t_h dtheta^h.

Note that because we explicitly represent the matrices t_i, the
parameters theta^i must be scalars; there is no other matrix
representation of a linear map from a rank-n tensor into matrices for
n > 0.

XXX Replace the computational representation of the derivatives by a
function that computes the increment in the covariance matrix, rather
than a function that returns a matrix whose product with an increment
in theta is an increment in the covariance matrix.
"""

from __future__ import division

import numpy as np
import scipy.spatial.distance

from venture.lite.utils import override
from venture.lite.function import ParamLeaf
from venture.lite.function import ParamProduct


class Kernel(object):
  def __init__(self, *args, **kwargs):
    raise NotImplementedError
  def __repr__(self):
    raise NotImplementedError
  @property
  def parameters(self):
    raise NotImplementedError('Non-differentiable kernel: %r' % (self,))
  def f(self, X, Y):
    raise NotImplementedError
  def df_theta(self, X, Y):
    raise NotImplementedError
  def df_x(self, x, Y):
    raise NotImplementedError


class const(Kernel):
  """Constant kernel: everywhere equal to c."""

  @override(Kernel)
  def __init__(self, c):
    self._c = c

  @override(Kernel)
  def __repr__(self):
    return 'CONST(%r)' % (self._c,)

  @property
  @override(Kernel)
  def parameters(self):
    return [ParamLeaf()]

  @override(Kernel)
  def f(self, X, Y):
    c = self._c
    return c*np.ones((len(Y), len(X)))

  @override(Kernel)
  def df_theta(self, X, Y):
    k = self.f(X, Y)
    return (k, [np.ones(k.shape)])

  @override(Kernel)
  def df_x(self, x, Y):
    k = self.f(np.array([x]), Y)
    dk = [np.zeros((1, len(Y)))]*np.asarray(x).reshape(-1).shape[0]
    return (k, dk)


class Isotropic(Kernel):
  """Isotropic kernel: k(x, y) = k_r2(|x - y|^2), for some k_r2."""

  def k_r2(self, r2):
    raise NotImplementedError
  def ddtheta_k_r2(self, r2):
    raise NotImplementedError
  def ddr2_k_r2(self, r2):
    raise NotImplementedError

  @override(Kernel)
  def f(self, X, Y):
    # XXX Use _isotropic.
    f = self.k_r2
    X = X.reshape(len(X), -1)
    Y = Y.reshape(len(Y), -1)
    return f(scipy.spatial.distance.cdist(X, Y, 'sqeuclidean'))

  @override(Kernel)
  def df_theta(self, X, Y):
    return _isotropic(self.ddtheta_k_r2, X, Y)

  @override(Kernel)
  def df_x(self, x, Y):
    # For x, y_j in R^m, consider varying only x, so that dy_j = 0 for
    # all j.  Define
    #
    #   r_j^2 = |x - y_j|^2 = \sum_nu (x^nu - y_j^nu)^2,
    #
    # so that
    #
    #   d(r_j^2) = \sum_nu 2 (x^nu - y_j^nu) dx^nu = 2 (x - y_j)^T dx.
    #
    # An isotropic covariance kernel k(x, y_j) is given by a function
    # kappa of the distance r_j, k(x, y_j) = kappa(r_j^2); hence
    #
    #   d k(x, y_j) = d kappa(r_j^2) = kappa'(r_j^2) d(r_j^2)
    #     = kappa'(r_j^2) 2 (x - y_j)^T dx.
    #
    # Thus, d/dx k(x, y_j), i.e. the dx component of d k(x, y_j), is
    # the row vector
    #
    #   kappa'(r_j^2) 2 (x - y_j)^T,
    #
    # where kappa'(r_j^2) is a scalar.
    #
    # If k(x, Y) is the row [k(x, y_1), k(x, y_2), ..., k(x, y_n)],
    # our job is to return the matrix k(x, Y) and a list of the dx^nu
    # components of d k(x, Y), namely a list of the columns (d/dx^nu
    # k(x, y_1), d/dx^nu k(x, y_2), ..., d/dx^nu k(x, y_n)).
    #
    # However, we need to compute not the row d/dx k(x, y_j), but the
    # whole matrix d/dx k(x, Y) = (d/dx k(x, y_1), d/dx k(x, y_2),
    # ..., d/dx k(x, y_n)), and return its representation as an array
    # of the columns d/dx^nu k(x, Y).
    #
    # For a matrix r2 of distances (r_ij^2)_ij, the function df(r2)
    # simultaneously computes the matrices (kappa(r_ij^2))_ij and
    # (kappa'(r_ij^2))_ij.  In this case, for a single left-hand input
    # point x, i = 1 always -- there is only one row.

    # Construct a single-element array of left-hand input points.
    X = np.array([x])

    # Make sure X and Y are rank-2 arrays, i.e. arrays of input
    # points where an input point is an array of scalars, as required
    # by cdist.
    #
    X = X.reshape(len(X), -1)
    Y = Y.reshape(len(Y), -1)

    # Compute the matrix r2 of all squared distances between x and
    # every point in the array Y.  Since X has only one point, the
    # matrix r2 has only one row:
    #
    #   r2 = [r_11^2   r_12^2   r_13^2   ...    r_1n^2],
    #
    # where r_1j^2 = |x - y_j|^2.
    #
    r2 = scipy.spatial.distance.cdist(X, Y, 'sqeuclidean')

    # Compute the array (2 (x^nu - y_j^nu))_j,nu of the pointwise
    # differences
    #
    #   2 (x - y_j);
    #
    # transpose it to give the array (2 (x^nu - y_j^nu))_nu,j of the
    # coordinatewise differences
    #
    #   2 (x^nu - Y^nu),
    #
    # so that the nu^th element of dr2 is the partial derivative with
    # respect to the nu^th input space coordinate of the array of
    # squared distances (r_1^2, r_2^2, ..., r_n^2), namely
    #
    #   (d/dx^nu r_1^2, d/dx^nu r_2^2, ..., d/dx^nu r_n^2)
    #   = (2 (x^nu - y_1),
    #      2 (x^nu - y_2),
    #      ...,
    #      2 (x^nu - y_n)).
    #
    dr2 = 2*(x - Y).T           # array of increments in r^2 matrix

    # Compute the covariance matrix k = (kappa(r_ij^2))_ij and the
    # derivative matrix f_ = (kappa'(r_ij^2))_ij.  Note that i = 1, so
    # that both k and f_ are single-row matrices.
    #
    k, f_ = self.ddr2_k_r2(r2)  # matrix and increment in matrix

    # Yield the covariance matrix k and the list of partial
    # derivatives [(kappa'(r_ij^2) d/dx^nu r_ij^2)_ij]_nu by computing
    # the elementwise product of the matrix f_ = (kappa'(r_ij^2))_ij
    # with the matrix dr2[nu] = (d/dx^nu r_ij^2)_ij for each nu.
    #
    return (k, [f_*dr2_k for dr2_k in dr2])


def _isotropic(f, X, Y):
  X = X.reshape(len(X), -1)
  Y = Y.reshape(len(Y), -1)
  return f(scipy.spatial.distance.cdist(X, Y, 'sqeuclidean'))


class delta(Isotropic):
  """Delta kernel: 1 if r^2 is at most tolerance, else 0."""

  @override(Isotropic)
  def __init__(self, tolerance):
    self._tolerance = tolerance

  @override(Isotropic)
  def __repr__(self):
    return 'DELTA(t^2=%r)' % (self._tolerance,)

  @property
  @override(Isotropic)
  def parameters(self):
    return [ParamLeaf()]

  @override(Isotropic)
  def k_r2(self, r2):
    tolerance = self._tolerance
    return 1.*(r2 <= tolerance)


def _deltoid(r2, t2, s):
  return -np.expm1(-(r2/t2)**(-s/2))


# First, note that since d(a^b) = a^b [log a db + (b/a) da],
#
#       d (r/t)^{-s} = (r/t)^{-s} [log (r/t) ds + s/(r/t) d(r/t)]
#         = (r/t)^{-s} [log (r/t) ds + (s t / r) (t dr - r dt)/t^2]
#         = (r/t)^{-s} [log (r/t) ds + (s t^2 / r t^2) dr - (s t r / r t^2) dt]
#         = (r/t)^{-s} [log (r/t) ds + (s/r) dr - (s/t) dt].
#
# Since d(x^2) = 2 x dx, we can write this in terms of the squared
# radius and tolerance parameters:
#
#         = (r^2/t^2)^{-s/2}
#             [(1/2) log (r^2/t^2) ds + (s / 2 r^2) dr^2 - (s / 2 t^2) dt^2]
#         = (1/2) (r^2/t^2){-s/2}
#             [log (r^2/t^2) ds + (s/r^2) dr^2 - (s/t^2) dt^2].
#
# Then
#
#       d k(r^2, t^2, s)
#         = d (1 - e^{-(r/t)^{-s}})
#         = d e^{-(r/t)^{-s}}
#         = e^{-(r/t)^{-s}} d [-(r/t)^{-s}]
#         = -e^{-(r/t)^{-s}} (r/t)^{-s} [log (r/t) ds + (s/r) dr - (s/t) dt]
#         = (-1/2) e^{-(r^2/t^2)^{-s/2}} (r^2/t^2)^{-s/2}
#             [log (r^2/t^2) ds + (s/r^2) dr^2 - (s/t^2) dt^2].


class deltoid(Isotropic):
  """Deltoid kernel: 1 - e^{-1/(r/t)^s}.

  Shaped kinda like a sigmoid, but not quite.
  Behaves kinda like a delta, but smoothly.

  Tolerance is in units of squared distance and determines at what
  squared radius the covariance kernel attains 1/2.
  """

  @override(Isotropic)
  def __init__(self, tolerance, steepness):
    self._tolerance = tolerance
    self._steepness = steepness

  @override(Isotropic)
  def __repr__(self):
    return 'DELTOID(t^2=%r, s=%r)' % (self._tolerance, self._steepness)

  @property
  @override(Isotropic)
  def parameters(self):
    return [ParamLeaf(), ParamLeaf()]

  @override(Isotropic)
  def k_r2(self, r2):
    return _deltoid(r2, self._tolerance, self._steepness)

  @override(Isotropic)
  def ddtheta_k_r2(self, r2):
    t2 = self._tolerance
    s = self._steepness
    u = -(r2/t2)**(-s/2)
    v = 0.5*np.exp(u)*u
    k = -np.expm1(u)
    dk_dt2 = np.where(r2 == 0, np.zeros_like(r2), -v*s/t2)
    dk_ds = np.where(r2 == 0, np.zeros_like(r2), v*np.log(r2/t2))
    assert np.all(np.isfinite(dk_dt2)), '%r' % (dk_dt2,)
    assert np.all(np.isfinite(dk_ds)), '%r' % (dk_ds,)
    return (k, [dk_dt2, dk_ds])

  @override(Isotropic)
  def ddr2_k_r2(self, r2):
    t2 = self._tolerance
    s = self._steepness
    u = -(r2/t2)**(-s/2)
    k = -np.expm1(u)
    # For the self-covariances, just give zero derivative because we
    # do not consider moving the inputs off the diagonal line x = y.
    # XXX Consider making this generic for all covariance derivatives
    # with respect to an input.
    dk = np.where(r2 == 0, np.zeros_like(r2), 0.5*np.exp(u)*u*s/r2)
    assert np.all(np.isfinite(dk)), '%r' % (dk,)
    return (k, dk)


def _on_ring(x, a, b, inner, middle, outer):
  return np.where(x <= a, inner, np.where(x < b, middle, outer))

def _bump(r2, t_0, t_1):
  # np.exp(1 - 1/(1 - ((r2 - t_0)/(t_1 - t_0))))
  return _on_ring(r2, t_0, t_1,
    1 + np.zeros_like(r2),
    np.exp(1 - (t_1 - t_0)/(t_1 - r2)),
    np.zeros_like(r2))


class bump(Isotropic):
  """Bump kernel: 1 if r^2 < min_tolerance, 0 if r^2 > max_tolerance."""

  @override(Isotropic)
  def __init__(self, min_tolerance, max_tolerance):
    self._min_tolerance = min_tolerance
    self._max_tolerance = max_tolerance

  @override(Isotropic)
  def __repr__(self):
    return 'BUMP(min=%r, max=%r)' % (self._min_tolerance, self._max_tolerance)

  @property
  @override(Isotropic)
  def parameters(self):
    return [ParamLeaf(), ParamLeaf()]

  @override(Isotropic)
  def k_r2(self, r2):
    min_tolerance = self._min_tolerance
    max_tolerance = self._max_tolerance
    return _bump(r2, min_tolerance, max_tolerance)

  @override(Isotropic)
  def ddtheta_k_r2(self, r2):
    t_0 = self._min_tolerance
    t_1 = self._max_tolerance
    k = _bump(r2, t_0, t_1)
    dk_dt0 = _on_ring(r2, t_0, t_1,
      np.zeros_like(r2), k/(t_1 - r2), np.zeros_like(r2))
    dk_dt1 = _on_ring(r2, t_0, t_1,
      np.zeros_like(r2), k*(r2 - t_0)/(t_1 - r2)**2, np.zeros_like(r2))
    assert np.all(np.isfinite(dk_dt0)), '%r' % (dk_dt0,)
    assert np.all(np.isfinite(dk_dt1)), '%r' % (dk_dt1,)
    return (k, [dk_dt0, dk_dt1])

  @override(Isotropic)
  def ddr2_k_r2(self, r2):
    t_0 = self._min_tolerance
    t_1 = self._max_tolerance
    w = t_1 - t_0
    k = _bump(r2, t_0, t_1)
    dk_dr2 = _on_ring(r2, t_0, t_1,
      np.zeros_like(r2), -k*w/(t_1 - r2)**2, np.zeros_like(r2))
    assert np.all(np.isfinite(dk_dr2)), '%r' % (dk_dr2,)
    return (k, dk_dr2)


def _se(r2, l2):
  return np.exp(-0.5 * r2 / l2)

def _d_se_l2(r2, l2):
  """d/d(l^2) of squared exponential kernel."""
  k = _se(r2, l2)
  return (k, k * 0.5 * r2 / (l2*l2))

def _d_se_r2(r2, l2):
  """d/d(r^2) of squared exponential kernel."""
  k = _se(r2, l2)
  return (k, k * -0.5 / l2)


class se(Isotropic):
  """Squared-exponential kernel: e^(-r^2 / (2 l^2))"""

  @override(Isotropic)
  def __init__(self, l2):
    self._l2 = l2

  @override(Isotropic)
  def __repr__(self):
    return 'SE(l^2=%r)' % (self._l2,)

  @property
  @override(Isotropic)
  def parameters(self):
    return [ParamLeaf()]

  @override(Isotropic)
  def k_r2(self, r2):
    l2 = self._l2
    return _se(r2, l2)

  @override(Isotropic)
  def ddtheta_k_r2(self, r2):
    l2 = self._l2
    k, dk = _d_se_l2(r2, l2)
    return (k, [dk])

  @override(Isotropic)
  def ddr2_k_r2(self, r2):
    l2 = self._l2
    k, dk = _d_se_r2(r2, l2)
    return (k, dk)


class periodic(Isotropic):
  """Periodic kernel: e^(-(2 sin(2pi r / T))^2 / (2 l^2))"""

  @override(Isotropic)
  def __init__(self, l2, T):
    self._l2 = l2
    self._T = T

  @override(Isotropic)
  def __repr__(self):
    return 'PER(l^2=%r, T=%r)' % (self._l2, self._T)

  @property
  @override(Isotropic)
  def parameters(self):
    return [ParamLeaf(), ParamLeaf()]

  @override(Isotropic)
  def k_r2(self, r2):
    pi = np.pi
    sin = np.sin
    sqrt = np.sqrt
    l2 = self._l2
    T = self._T

    d = 2*sin(2*pi*sqrt(r2)/T)
    return _se(d**2, l2)

  @override(Isotropic)
  def ddtheta_k_r2(self, r2):
    cos = np.cos
    pi = np.pi
    sin = np.sin
    sqrt = np.sqrt
    l2 = self._l2
    T = self._T

    t = 2*pi*sqrt(r2)/T
    d2 = (2*sin(t))**2
    k, dk_l2 = _d_se_l2(d2, l2)
    return (k, [dk_l2, k * (4/(l2*T)) * t * sin(t) * cos(t)])

  @override(Isotropic)
  def ddr2_k_r2(self, r2):
    cos = np.cos
    pi = np.pi
    sin = np.sin
    sqrt = np.sqrt
    l2 = self._l2
    T = self._T

    r = sqrt(r2)
    t = 2*pi*r/T
    sin_t = sin(t)
    d2 = (2*sin_t)**2
    k, dk_d2 = _d_se_r2(d2, l2)
    dk_r2 = np.where(r2 == 0, np.zeros_like(r2), dk_d2*8*pi*sin_t*cos(t)/(T*r))
    assert np.all(np.isfinite(dk_r2)), '%r' % (dk_r2,)
    return (k, dk_r2)


class rq(Isotropic):
  """Rational quadratic kernel: (1 + r^2/(2 alpha l^2))^-alpha"""

  @override(Isotropic)
  def __init__(self, l2, alpha):
    self._l2 = l2
    self._alpha = alpha

  @override(Isotropic)
  def __repr__(self):
    return 'RQ(l^2=%r, alpha=%r)' % (self._l2, self._alpha)

  @override(Isotropic)
  def k_r2(self, r2):
    l2 = self._l2
    alpha = self._alpha
    return np.power(1 + r2/(2 * alpha * l2), -alpha)


class matern(Isotropic):
  """Matérn kernel with squared length-scale l2 and nu = df/2."""

  @override(Isotropic)
  def __init__(self, l2, df):
    import scipy.special
    nu = df/2
    c = np.exp((1 - nu)*np.log(2) - scipy.special.gammaln(nu))
    self._c = c
    self._df = df
    self._l2 = l2

  @override(Isotropic)
  def __repr__(self):
    return 'MATERN(l^2=%r, df=%r)' % (self._l2, self._df)

  # @property
  # @override(Isotropic)
  # def parameters(self):
  #   return [ParamLeaf(), ParamLeaf()]

  @override(Isotropic)
  def k_r2(self, r2):
    import scipy.special
    c = self._c
    df = self._df
    l2 = self._l2
    q = np.sqrt(df*r2/l2)
    return c * np.power(q, nu) * scipy.special.kv(nu, q)


class matern_32(Isotropic):
  """Matérn kernel specialized with three degrees of freedom."""

  @override(Isotropic)
  def __init__(self, l2):
    self._l2 = l2

  @override(Isotropic)
  def __repr__(self):
    return 'MATERN(l^2=%r, df=3)' % (self._l2,)

  # @property
  # @override(Isotropic)
  # def parameters(self):
  #   return [ParamLeaf()]

  @override(Isotropic)
  def k_r2(self, r2):
    l2 = self._l2
    q = np.sqrt(3*r2/l2)
    return (1 + q)*np.exp(-q)


class matern_52(Isotropic):
  """Matérn kernel specialized with three degrees of freedom."""

  @override(Isotropic)
  def __init__(self, l2):
    self._l2 = l2

  @override(Isotropic)
  def __repr__(self):
    return 'MATERN(l^2=%r, df=5)' % (self._l2,)

  @property
  @override(Isotropic)
  def parameters(self):
    return [ParamLeaf()]

  @override(Isotropic)
  def k_r2(self, r2):
    l2 = self._l2
    q2 = 5*r2/l2
    q = np.sqrt(q2)
    return (1 + q + q2/3)*np.exp(-q)


class linear(Kernel):
  """Linear covariance kernel: k(x, y) = (x - c) (y - c)."""

  @override(Kernel)
  def __init__(self, c):
    self._c = c

  @override(Kernel)
  def __repr__(self):
    return 'LIN(origin=%r)' % (self._c,)

  @property
  @override(Kernel)
  def parameters(self):
    c = self._c
    if np.asarray(c).ndim:
      return [ParamProduct([ParamLeaf() for _ in c])]
    else:
      return [ParamLeaf()]

  @override(Kernel)
  def f(self, X, Y):
    c = self._c
    if np.asarray(c).ndim:
      return np.inner(X - c, Y - c)
    else:
      return np.outer(X - c, Y - c)

  @override(Kernel)
  def df_theta(self, X, Y):
    k = self.f(X, Y)

    c = self._c
    c = np.asarray(c).reshape(-1)
    assert c.ndim == 1, '%r' % (c,)
    d = c.shape[0]
    X = X.reshape(len(X), -1)
    Y = Y.reshape(len(Y), -1)

    dk = [None] * d
    for nu in xrange(d):
      dk[nu] = 2*c[nu] * np.ones((len(X), len(Y)))
      for i in xrange(len(X)):
        dk[nu][i,:] -= Y[:,nu]
      for j in xrange(len(Y)):
        dk[nu][:,j] -= X[:,nu]

    return (k, dk)

  @override(Kernel)
  def df_x(self, x, Y):
    X = np.array([x])
    k = self.f(X, Y)

    c = self._c
    c = np.asarray(c).reshape(-1)
    assert c.ndim == 1
    d = c.shape[0]
    X = X.reshape(len(X), -1)
    Y = Y.reshape(len(Y), -1)

    dk = [None] * d
    for nu in xrange(d):
      dk[nu] = -c[nu] * np.ones((len(X), len(Y)))
      for i in xrange(len(X)):
        dk[nu][i,:] += Y[:,nu]

    return (k, dk)


class bias(Kernel):
  """Kernel K biased by the constant squared bias s^2.

  Every covariance, including variance/self-covariance, has s^2 added.
  """

  @override(Kernel)
  def __init__(self, s2, K):
    self._s2 = s2
    self._K = K

  @override(Kernel)
  def __repr__(self):
    return '(%r + %r)' % (self._s2, self._K)

  @property
  @override(Kernel)
  def parameters(self):
    return [ParamLeaf(), ParamProduct(self._K.parameters)]

  @override(Kernel)
  def f(self, X, Y):
    s2 = self._s2
    K = self._K
    return s2 + K.f(X, Y)

  @override(Kernel)
  def df_theta(self, X, Y):
    s2 = self._s2
    K = self._K
    k, dk = K.df_theta(X, Y)
    return (s2 + k, [np.ones(k.shape)] + dk)

  @override(Kernel)
  def df_x(self, x, Y):
    s2 = self._s2
    K = self._K
    k, dk = K.df_x(x, Y)
    return (s2 + k, dk)


class scale(Kernel):
  """Kernel K scaled by squared output factor s^2."""

  @override(Kernel)
  def __init__(self, s2, K):
    self._s2 = s2
    self._K = K

  @override(Kernel)
  def __repr__(self):
    return '(%r*%r)' % (self._s2, self._K)

  @property
  @override(Kernel)
  def parameters(self):
    return [ParamLeaf(), ParamProduct(self._K.parameters)]

  @override(Kernel)
  def f(self, X, Y):
    s2 = self._s2
    K = self._K
    return s2 * K.f(X, Y)

  @override(Kernel)
  def df_theta(self, X, Y):
    s2 = self._s2
    K = self._K
    k, dk = K.df_theta(X, Y)
    return (s2 * k, [k] + [s2*dk_i for dk_i in dk])

  @override(Kernel)
  def df_x(self, x, Y):
    s2 = self._s2
    K = self._K
    k, dk = K.df_x(x, Y)
    assert np.all(np.isfinite(dk_i) for dk_i in dk)
    return (s2 * k, [s2*dk_i for dk_i in dk])


class sum(Kernel):
  """Sum of kernels K and H."""

  @override(Kernel)
  def __init__(self, K, H):
    self._K = K
    self._H = H

  @override(Kernel)
  def __repr__(self):
    return '(%r + %r)' % (self._K, self._H)

  @property
  @override(Kernel)
  def parameters(self):
    K_shape = ParamProduct(self._K.parameters)
    H_shape = ParamProduct(self._H.parameters)
    return [K_shape, H_shape]

  @override(Kernel)
  def f(self, X, Y):
    K = self._K
    H = self._H
    return K.f(X, Y) + H.f(X, Y)

  @override(Kernel)
  def df_theta(self, X, Y):
    K = self._K
    H = self._H
    k, dk = K.df_theta(X, Y)
    h, dh = H.df_theta(X, Y)
    return (k + h, dk + dh)

  @override(Kernel)
  def df_x(self, x, Y):
    K = self._K
    H = self._H
    k, dk = K.df_x(x, Y)
    h, dh = H.df_x(x, Y)
    return (k + h, [dk_i + dh_i for dk_i, dh_i in zip(dk, dh)])


class product(Kernel):
  """Product of kernels K and H."""

  @override(Kernel)
  def __init__(self, K, H):
    self._K = K
    self._H = H

  @override(Kernel)
  def __repr__(self):
    return '(%r*%r)' % (self._K, self._H)

  @property
  @override(Kernel)
  def parameters(self):
    K_shape = ParamProduct(self._K.parameters)
    H_shape = ParamProduct(self._H.parameters)
    return [K_shape, H_shape]

  @override(Kernel)
  def f(self, X, Y):
    K = self._K
    H = self._H
    return K.f(X, Y) * H.f(X, Y)

  @override(Kernel)
  def df_theta(self, X, Y):
    K = self._K
    H = self._H
    k, dk = K.df_theta(X, Y)
    h, dh = H.df_theta(X, Y)
    return (k*h, [dk_i*h for dk_i in dk] + [k*dh_i for dh_i in dh])

  @override(Kernel)
  def df_x(self, x, Y):
    K = self._K
    H = self._H
    k, dk = K.df_x(x, Y)
    h, dh = H.df_x(x, Y)
    return (k*h, [dk_i*h + k*dh_i for dk_i, dh_i in zip(dk, dh)])
