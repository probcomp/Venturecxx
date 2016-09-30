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
A, X_1 = (x_11, x_12, ..., x_1m) and X_2 = (x_21, x_22, ..., x_2l),
and returns a matrix

    [k(x_11, x_21), k(x_11, x_22), ..., k(x_11, x_2l);
     k(x_12, x_21), k(x_12, x_22), ..., k(x_12, x_2l);
           :              :        .          :
           :              :         .         :
     k(x_1m, x_21), k(x_1m, x_22), ..., k(x_1m, x_2l)]

of all covariances between all pairwise elements in X_1 and X_2.

For a covariance kernel k_theta parametrized by some theta = (theta^1,
theta^2, ..., theta^h), the derivative of the covariance kernel with
respect to theta is computationally represented by a function that
takes two arrays X_1 and X_2 in A and returns an array of the h
partial derivatives of k_theta(X_1, X_2) with respect to theta -- that
is, returns an array of h matrices [t_1, t_2, ..., t_h], so that t_i
maps an increment in theta^i to an increment in the covariance matrix
between X_1 and X_2:

    d k_theta(X_1, X_2) = t_1 dtheta^1 + t_2 dtheta^2 + ... + t_h dtheta^h.

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
  def k(X_1, X_2):
    return c*np.ones((len(X_1), len(X_2)))
  return k

def ddtheta_const(c):
  f = const(c)
  def dk_const_dtheta(X_1, X_2):
    k = f(X_1, X_2)
    return (k, [np.ones(k.shape)])
  return dk_const_dtheta

def ddx_const(c):
  k = const(c)
  def dk_const_dx(x_1, X_2):
    return (k(np.array([x_1]), X_2), np.zeros(x_1.shape[0]))
  return dk_const_dx

# Isotropic covariance kernels

def isotropic(f):
  """Isotropic kernel: k(x_1, x_2) = f(||x_1 - x_2||^2).

  Given a function f(r) on a matrix of all pairwise distances between
  two sets of input points, yields a covariance kernel k(X_1, X_2) on
  two arrays of input points.
  """
  def k(X_1, X_2):
    X_1 = X_1.reshape(len(X_1), -1)
    X_2 = X_2.reshape(len(X_2), -1)
    return f(scipy.spatial.distance.cdist(X_1, X_2, 'sqeuclidean'))
  return k

def ddtheta_isotropic(df_theta):
  """Isotropic kernel derivative with respect to parameters.

  Given a function df_theta(r^2) that maps a matrix of squared
  distances between every pair of points in two arrays of inputs to a
  matrix of d/dtheta kappa({r_ij}^2) covariance derivatives, yields a
  covariance kernel derivative dk_theta(X_1, X_2) that maps two arrays
  of input points to a matrix of d/dtheta k(x_1, x_2) covariance
  derivatives.
  """
  return isotropic(df_theta)

def ddx_isotropic(df):
  """Isotropic kernel partial derivative with respect to input point.

  Given a function df_r2(r2) that maps a vector of squared distances
  to a vector of derivatives with respect to squared distance, yields
  a covariance kernel partial derivative dk_x(x_1, X_2) that maps a
  point x_1 and an array of points X_2 to a vector of partial
  derivatives with respect to x_1 at each of the pairs (x_1, x_2i).
  """
  def ddx_k(x_1, X_2):
    # Let x_1 = u and X_2 = (v_1, v_2, ..., v_n), for u, v_j in R^m.
    # Consider varying only u, so that dv_j = 0 for all j.  Define
    #
    #   r_j^2 = |u - v_j|^2 = \sum_nu (u^nu - v_j^nu)^2,
    #
    # so that
    #
    #   d(r_j^2) = \sum_nu 2 (u^nu - v_j^nu) du^nu = 2 (u - v_j)^T du.
    #
    # An isotropic covariance kernel k(u, v_j) is given by a function
    # kappa of the distance r_j, k(u, v_j) = kappa(r_j^2); hence
    #
    #   d k(u, v_j) = d kappa(r_j^2) = kappa'(r_j^2) d(r_j^2)
    #     = kappa'(r_j^2) 2 (u - v_j)^T du.
    #
    # Thus, d/du k(u, v_j), i.e. the du component of d k(u, v_j), is
    # the row vector
    #
    #   kappa'(r_j^2) 2 (u - v_j)^T,
    #
    # where kappa'(r_j^2) is a scalar.
    #
    # If k(u, V) is the row [k(u, v_1), k(u, v_2), ..., k(u, v_n)],
    # our job is to return the matrix k(u, V) and a list of the du^nu
    # components of d k(u, V), namely a list of the columns (d/du^nu
    # k(u, v_1), d/du^nu k(u, v_2), ..., d/du^nu k(u, v_n)).
    #
    # However, we need to compute not the row d/du k(u, v_i), but the
    # whole matrix d/du k(u, V) = (d/du k(u, v_1), d/du k(u, v_2),
    # ..., d/du k(u, v_n)), and return its representation as an array
    # of the columns d/du^nu k(u, V).
    #
    # For a matrix r2 of distances (r_ij^2)_ij, the function df(r2)
    # simultaneously computes the matrices (kappa(r_ij^2))_ij and
    # (kappa'(r_ij^2))_ij.  In this case, for a single left-hand input
    # point x_1, i = 1 always -- there is only one row.

    # Construct a single-element array of left-hand input points.
    X_1 = np.array([x_1])

    # Make sure X_1 and X_2 are rank-2 arrays, i.e. arrays of input
    # points where an input point is an array of scalars, as required
    # by cdist.
    #
    X_1 = X_1.reshape(len(X_1), -1)
    X_2 = X_2.reshape(len(X_2), -1)

    # Compute the matrix r2 of all squared distances between x_1 and
    # every point in the array X_2.  Since X_1 has only one point, the
    # matrix r2 has only one row:
    #
    #   r2 = [r_11^2   r_12^2   r_13^2   ...    r_1n^2],
    #
    # where r_1j^2 = |x_1 - X_2[j]|^2.
    #
    r2 = scipy.spatial.distance.cdist(X_1, X_2, 'sqeuclidean')

    # Compute the array (2 (x_1^nu - X_2[j]^nu))_j,nu of the
    # pointwise differences
    #
    #   2 (x_1 - X_2[j]);
    #
    # transpose it to give the array (2 (x_1^nu - X_2[j]^nu))_nu,j of
    # the coordinatewise differences
    #
    #   2 (x_1^nu - X_2^nu),
    #
    # so that the nu^th element of dr2 is the partial derivative with
    # respect to the nu^th input space coordinate of the array of
    # squared distances (r_1^2, r_2^2, ..., r_n^2), namely
    #
    #   (d/dx_1^nu r_1^2, d/dx_1^nu r_2^2, ..., d/dx_1^nu r_n^2)
    #   = (2 (x_1^nu - X_2[1]),
    #      2 (x_1^nu - X_2[2]),
    #      ...,
    #      2 (x_1^nu - X_2[n])).
    #
    dr2 = 2*(x_1 - X_2).T       # array of increments in r^2 matrix

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

def _bump(r2, t, s):
  return np.exp(-t/(r2**(s/2.)))

def bump(tolerance, steepness):
  """Bump kernel: e^{-t/r^s}"""
  def f(r2):
    return _bump(r2, tolerance, steepness)
  return isotropic(f)

def ddtheta_bump(tolerance, steepness):
  def df_theta(r2):
    # d/dt e^{-t/r^s} = -e^{-t/r^s}/r^s
    # d/ds e^{-t/r^s} = e^{-t/r^s} (-t) d/ds r^{-s}
    #   = e^{-t/r^s} (-t) (-log r) r^{-s}
    #   = e^{-t/r^s} t r^{-s} log r
    t = tolerance
    s = steepness
    r_s = r2**(-s/2.)
    k = np.exp(-t*r_s)
    return (k, [-k*r_s, k*t*r_s*np.log(r2)/2.])
  return ddtheta_isotropic(df_theta)

def ddx_bump(tolerance, steepness):
  def df_r2(r2):
    # d/d{r^2} e^{-t/r^s} = e^{-t/r^s} s t / [2 (r^2)^{s/2 + 1}]
    #   = e^{-t/r^s} s t r^{-s} / [2 r^2]
    t = tolerance
    s = steepness
    r_s = r2**(-s/2.)
    k = np.exp(-t*r_s)
    return (k, -k*s*t*r_s/(2*r2))
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
  return ddtheta_isotropic(df)

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

def linear(x):
  """Linear covariance kernel: k(x_1, x_2) = (x_1 - x) (x_2 - x)."""
  def k(X_1, X_2):
    if np.asarray(x).ndim:
      return np.inner(X_1 - x, X_2 - x)
    else:
      return np.outer(X_1 - x, X_2 - x)
  return k

def ddtheta_linear(x):
  f = linear(x)
  x = np.asarray(x).reshape(-1)

  def dk_linear_dtheta(X_1, X_2):
    k = f(X_1, X_2)

    assert x.ndim == 1, '%r' % (x,)
    d = x.shape[0]
    X_1 = X_1.reshape(len(X_1), -1)
    X_2 = X_2.reshape(len(X_2), -1)

    dk = [None] * d
    for nu in xrange(d):
      dk[nu] = 2*x[nu] * np.ones((len(X_1), len(X_2)))
      for i in xrange(len(X_1)):
        dk[nu][i,:] -= X_2[:,nu]
      for j in xrange(len(X_2)):
        dk[nu][:,j] -= X_1[:,nu]

    return (k, dk)

  return dk_linear_dtheta

def ddx_linear(x):
  f = linear(x)
  x = np.asarray(x).reshape(-1)

  def dk_linear_dx(x_1, X_2):
    X_1 = np.array([x_1])
    k = f(X_1, X_2)

    assert x.ndim == 1
    d = x.shape[0]
    X_1 = X_1.reshape(len(X_1), -1)
    X_2 = X_2.reshape(len(X_2), -1)

    dk = [None] * d
    for nu in xrange(d):
      dk[nu] = -x[nu] * np.ones((len(X_1), len(X_2)))
      for i in xrange(len(X_1)):
        dk[nu][i,:] += X_2[:,nu]

    return (k, dk)

  return dk_linear_dx

# Composite covariance kernels

def bias(s2, k):
  """Kernel k biased by the constant squared bias s^2.

  Every covariance, including variance/self-covariance, has s^2 added.
  """
  return lambda X_1, X_2: s2 + k(X_1, X_2)

def ddtheta_bias(s2, k):
  def dk_bias_dtheta(X_1, X_2):
    k12, dk12 = k.df_theta(X_1, X_2)
    return (s2 + k12, [np.ones(k12.shape)] + dk12)
  return dk_bias_dtheta

def ddx_bias(s2, k):
  def dk_bias_dx(x_1, X_2):
    k12, dk12 = k.df_x(x_1, X_2)
    return (s2 + k12, dk12)
  return dk_bias_dx

def scale(s2, k):
  """Kernel k scaled by squared output factor s^2."""
  return lambda X_1, X_2: s2 * k(X_1, X_2)

def ddtheta_scale(s2, k):
  def dk_scale_dtheta(X_1, X_2):
    k12, dk12 = k.df_theta(X_1, X_2)
    return (s2 * k12, [k12] + [s2*dk_i for dk_i in dk12])
  return dk_scale_dtheta

def ddx_scale(s2, k):
  def dk_scale_dx(x_1, X_2):
    k12, dk12 = k.df_x(x_1, X_2)
    return (s2 * k12, [s2*dk_i for dk_i in dk12])
  return dk_scale_dx

def sum(k_a, k_b):
  """Sum of kernels k_a and k_b."""
  return lambda X_1, X_2: k_a(X_1, X_2) + k_b(X_1, X_2)

def ddtheta_sum(k_a, k_b):
  def dk_sum_dtheta(X_1, X_2):
    ka, dka = k_a.df_theta(X_1, X_2)
    kb, dkb = k_a.df_theta(X_1, X_2)
    return (ka + kb, dka + dkb)
  return dk_sum_dtheta

def ddx_sum(k_a, k_b):
  def dk_sum_dx(x_1, X_2):
    ka, dka = k_a.df_x(x_1, X_2)
    kb, dkb = k_a.df_x(x_1, X_2)
    return (ka + kb, dka + dkb)
  return dk_sum_dx

def product(k_a, k_b):
  """Product of kernels k_a and k_b."""
  return lambda X_1, X_2: k_a(X_1, X_2) * k_b(X_1, X_2)

def ddtheta_product(k_a, k_b):
  def dk_product_dtheta(X_1, X_2):
    ka, dka = k_a.df_theta(X_1, X_2)
    kb, dkb = k_b.df_theta(X_1, X_2)
    return (ka*kb, [dk_ai*kb for dk_ai in dka] + [ka*dk_bi for dk_bi in dkb])
  return dk_product_dtheta

def ddx_product(k_a, k_b):
  def dk_product_dx(x_1, X_2):
    ka, dka = k_a.df_x(x_1, X_2)
    kb, dkb = k_b.df_x(x_1, X_2)
    return (ka*kb, [dk_ai*kb + ka*dk_bi for dk_ai, dk_bi in zip(dka, dkb)])
  return dk_product_dx
