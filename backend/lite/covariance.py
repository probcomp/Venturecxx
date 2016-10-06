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

import numpy as np
import scipy.spatial.distance

# Trivial covariance kernel

def const(c):
  """Constant kernel, everywhere equal to c."""
  def k(X, Y):
    return c*np.ones((len(Y), len(X)))
  return k

def ddtheta_const(c):
  f = const(c)
  def dk_const_dtheta(X, Y):
    k = f(X, Y)
    return (k, [np.ones(k.shape)])
  return dk_const_dtheta

def ddx_const(c):
  k = const(c)
  def dk_const_dx(x, Y):
    return (k(np.array([x]), Y), np.zeros(x.shape[0]))
  return dk_const_dx

# Isotropic covariance kernels

def isotropic(f):
  """Isotropic kernel: k(x, y) = f(||x - y||^2).

  Given a function f(r) on a matrix of all pairwise distances between
  two sets of input points, yields a covariance kernel k(X, Y) on two
  arrays of input points.
  """
  def k(X, Y):
    X = X.reshape(len(X), -1)
    Y = Y.reshape(len(Y), -1)
    return f(scipy.spatial.distance.cdist(X, Y, 'sqeuclidean'))
  return k

def ddtheta_isotropic(df_theta):
  """Isotropic kernel derivative with respect to parameters.

  Given a function df_theta(r^2) that maps a matrix of squared
  distances between every pair of points in two arrays of inputs to a
  matrix of d/dtheta kappa({r_ij}^2) covariance derivatives, yields a
  covariance kernel derivative dk_theta(X, Y) that maps two arrays of
  input points to a matrix of d/dtheta k(x, y) covariance derivatives.
  """
  return isotropic(df_theta)

def ddx_isotropic(df):
  """Isotropic kernel partial derivative with respect to input point.

  Given a function df_r2(r2) that maps a vector of squared distances
  to a vector of derivatives with respect to squared distance, yields
  a covariance kernel partial derivative dk_x(x, Y) that maps a point
  x and an array of points Y to a vector of partial derivatives with
  respect to x at each of the pairs (x, y_i).
  """
  def ddx_k(x, Y):
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
    k, f_ = df(r2)              # matrix and increment in matrix

    # Yield the covariance matrix k and the list of partial
    # derivatives [(kappa'(r_ij^2) d/dx^nu r_ij^2)_ij]_nu by computing
    # the elementwise product of the matrix f_ = (kappa'(r_ij^2))_ij
    # with the matrix dr2[nu] = (d/dx^nu r_ij^2)_ij for each nu.
    #
    return (k, [f_*dr2_k for dr2_k in dr2])
  return ddx_k

def delta(tolerance):
  """Delta kernel: 1, if r^2 is at most tolerance; else 0."""
  def f(r2):
    return 1.*(r2 <= tolerance)
  return isotropic(f)

def _deltoid(r2, t, s):
  return -np.expm1(-t/(r2**(s/2.)))

def deltoid(tolerance, steepness):
  """Deltoid kernel: 1 - e^{-t/r^s}.

  Shaped kinda like a sigmoid, but not quite.
  Behaves kinda like a delta, but smoothly.

  The tolerance parameter is currently hokey and will be replaced by a
  simple squared scale parameter.
  """
  def f(r2):
    return _deltoid(r2, tolerance, steepness)
  return isotropic(f)

def ddtheta_deltoid(tolerance, steepness):
  def df_theta(r2):
    # d/dt (1 - e^{-t/r^s}) = e^{-t/r^s}/r^s
    # d/ds (1 - e^{-t/r^s}) = -e^{-t/r^s} (-t) d/ds r^{-s}
    #   = -e^{-t/r^s} (-t) (-log r) r^{-s}
    #   = -e^{-t/r^s} t r^{-s} log r
    t = tolerance
    s = steepness
    r_s = r2**(-s/2.)
    k1 = np.exp(-t*r_s)
    # Where r^2 = 0, k is zero, and so should dk/dt and dk/ds be.  But
    # r_s will have infinities there, and log(0) and 0*inf both give
    # NaN where we want zero.  So explicitly give zero there.
    dk_dt = np.where(r2 == 0, np.zeros_like(r_s), k1*r_s)
    dk_ds = np.where(r2 == 0, np.zeros_like(r_s), -k1*t*r_s*np.log(r2)/2.)
    assert np.all(np.isfinite(dk_dt)), '%r' % (dk_dt,)
    assert np.all(np.isfinite(dk_ds)), '%r' % (dk_ds,)
    return (-np.expm1(-t*r_s), [dk_dt, dk_ds])
  return ddtheta_isotropic(df_theta)

def ddx_deltoid(tolerance, steepness):
  def df_r2(r2):
    # d/d{r^2} (1 - e^{-t/r^s}) = -e^{-t/r^s} s t / [2 (r^2)^{s/2 + 1}]
    #   = -e^{-t/r^s} s t r^{-s} / [2 r^2]
    t = tolerance
    s = steepness
    r_s = r2**(-s/2.)
    k = np.exp(-t*r_s)
    # For the self-covariances, just give zero derivative because we
    # do not consider moving the inputs off the diagonal line x = y.
    # XXX Consider making this generic for all covariance derivatives
    # with respect to an input.
    dk = np.where(r2 == 0, np.zeros_like(r2), -k*s*t*r_s/(2*r2))
    assert np.all(np.isfinite(dk)), '%r' % (dk,)
    return (k, dk)
  return ddx_isotropic(df_r2)

def _on_ring(x, a, b, inner, middle, outer):
  return np.where(x <= a, inner, np.where(x < b, middle, outer))

def _bump(r2, t_0, t_1):
  # np.exp(1 - 1/(1 - ((r2 - t_0)/(t_1 - t_0))))
  return _on_ring(r2, t_0, t_1,
    1 + np.zeros_like(r2),
    np.exp(1 - (t_1 - t_0)/(t_1 - r2)),
    np.zeros_like(r2))

def bump(min_tolerance, max_tolerance):
  """Bump kernel: 1 if r^2 < min_tolerance, 0 if r^2 > max_tolerance."""
  def f(r2):
    return _bump(r2, min_tolerance, max_tolerance)
  return isotropic(f)

def ddtheta_bump(min_tolerance, max_tolerance):
  def df_theta(r2):
    t_0 = min_tolerance
    t_1 = max_tolerance
    k = _bump(r2, t_0, t_1)
    dk_dt0 = _on_ring(r2, t_0, t_1,
      np.zeros_like(r2), k/(t_1 - r2), np.zeros_like(r2))
    dk_dt1 = _on_ring(r2, t_0, t_1,
      np.zeros_like(r2), k*(r2 - t_0)/(t_1 - r2)**2, np.zeros_like(r2))
    assert np.all(np.isfinite(dk_dt0)), '%r' % (dk_dt0,)
    assert np.all(np.isfinite(dk_dt1)), '%r' % (dk_dt1,)
    return (k, [dk_dt0, dk_dt1])
  return ddtheta_isotropic(df_theta)

def ddx_bump(min_tolerance, max_tolerance):
  def df_r2(r2):
    t_0 = min_tolerance
    t_1 = max_tolerance
    w = t_1 - t_0
    k = _bump(r2, t_0, t_1)
    dk_dr2 = -k*w/(t_1 - r2)**2
    assert np.all(np.isfinite(dk_dr2)), '%r' % (dk_dr2,)
    return (k, dk_dr2)
  return ddx_isotropic(df_r2)

def _se(r2, l2):
  return np.exp(-0.5 * r2 / l2)

def se(l2):
  """Squared-exponential kernel: e^(-r^2 / (2 l^2))"""
  return isotropic(lambda r2: _se(r2, l2))

def _d_se_l2(r2, l2):
  """d/d(l^2) of squared exponential kernel."""
  k = _se(r2, l2)
  return (k, k * 0.5 * r2 / (l2*l2))

def _d_se_r2(r2, l2):
  """d/d(r^2) of squared exponential kernel."""
  k = _se(l2, r2)
  return (k, k * -0.5 / l2)

def ddtheta_se(l2):
  def df_theta(r2):
    k, dk = _d_se_l2(r2, l2)
    return (k, [dk])
  return ddtheta_isotropic(df_theta)

def ddx_se(l2):
  def df_r2(r2):
    k, dk = _d_se_r2(r2, l2)
    return (k, dk)
  return ddx_isotropic(df_r2)

def periodic(l2, T):
  """Periodic kernel: e^(-(2 sin(2pi r / T))^2 / (2 l^2))"""
  sin = np.sin
  pi = np.pi
  sqrt = np.sqrt
  def f(r2):
    d = 2.*sin(2.*pi*sqrt(r2)/T)
    return _se(d**2, l2)
  return isotropic(f)

def ddtheta_periodic(l2, T):
  cos = np.cos
  pi = np.pi
  sin = np.sin
  sqrt = np.sqrt
  def df_theta(r2):
    t = 2.*pi*sqrt(r2)/T
    d2 = (2.*sin(t))**2
    k, dk_l2 = _d_se_l2(d2, l2)
    return (k, [dk_l2, k * (4/(l2*T)) * t * sin(t) * cos(t)])
  return ddtheta_isotropic(df_theta)

def ddx_periodic(l2, T):
  cos = np.cos
  pi = np.pi
  sin = np.sin
  sqrt = np.sqrt
  def df_r2(r2):
    t = 2.*pi*sqrt(r2)/T
    d2 = (2.*sin(t))**2
    k, dk_r2 = _d_se_r2(d2, l2)
    return (k, k * (8*pi/(l2*d)) * sin(t) * cos(t))
  return ddx_isotropic(df_r2)

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

def linear(c):
  """Linear covariance kernel: k(x, y) = (x - c) (y - c)."""
  def k(X, Y):
    if np.asarray(c).ndim:
      return np.inner(X - c, Y - c)
    else:
      return np.outer(X - c, Y - c)
  return k

def ddtheta_linear(c):
  f = linear(c)
  c = np.asarray(c).reshape(-1)

  def dk_linear_dtheta(X, Y):
    k = f(X, Y)

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

  return dk_linear_dtheta

def ddx_linear(c):
  f = linear(c)
  c = np.asarray(c).reshape(-1)

  def dk_linear_dx(x, Y):
    X = np.array([x])
    k = f(X, Y)

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

  return dk_linear_dx

# Composite covariance kernels

def bias(s2, K):
  """Kernel K biased by the constant squared bias s^2.

  Every covariance, including variance/self-covariance, has s^2 added.
  """
  return lambda X, Y: s2 + K(X, Y)

def ddtheta_bias(s2, K):
  def dk_bias_dtheta(X, Y):
    k, dk = K.df_theta(X, Y)
    return (s2 + k, [np.ones(k.shape)] + dk)
  return dk_bias_dtheta

def ddx_bias(s2, K):
  def dk_bias_dx(x, Y):
    k, dk = K.df_x(x, Y)
    return (s2 + k, dk)
  return dk_bias_dx

def scale(s2, K):
  """Kernel K scaled by squared output factor s^2."""
  return lambda X, Y: s2 * K(X, Y)

def ddtheta_scale(s2, K):
  def dk_scale_dtheta(X, Y):
    k, dk = K.df_theta(X, Y)
    return (s2 * k, [k] + [s2*dk_i for dk_i in dk])
  return dk_scale_dtheta

def ddx_scale(s2, K):
  def dk_scale_dx(x, Y):
    k, dk = K.df_x(x, Y)
    return (s2 * k, [s2*dk_i for dk_i in dk])
  return dk_scale_dx

def sum(K, H):
  """Sum of kernels K and H."""
  return lambda X, Y: K(X, Y) + H(X, Y)

def ddtheta_sum(K, H):
  def dk_sum_dtheta(X, Y):
    k, dk = K.df_theta(X, Y)
    h, dh = H.df_theta(X, Y)
    return (k + h, dk + dh)
  return dk_sum_dtheta

def ddx_sum(K, H):
  def dk_sum_dx(x, Y):
    k, dk = K.df_x(x, Y)
    h, dh = H.df_x(x, Y)
    return (k + h, dk + dh)
  return dk_sum_dx

def product(K, H):
  """Product of kernels K and H."""
  return lambda X, Y: K(X, Y) * H(X, Y)

def ddtheta_product(K, H):
  def dk_product_dtheta(X, Y):
    k, dk = K.df_theta(X, Y)
    h, dh = H.df_theta(X, Y)
    return (k*h, [dk_i*h for dk_i in dk] + [k*dh_i for dh_i in dh])
  return dk_product_dtheta

def ddx_product(K, H):
  def dk_product_dx(x, Y):
    k, dk = K.df_x(x, Y)
    h, dh = H.df_x(x, Y)
    return (k*h, [dk_i*h + k*dh_i for dk_i, dh_i in zip(dk, dh)])
  return dk_product_dx
