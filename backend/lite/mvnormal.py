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
import scipy.linalg as la

# XXX Use LDL decomposition instead of Cholesky so that we can handle
# merely positive-semidefinite, rather than positive-definite,
# covariance matrices.  Problem: neither numpy nor scipy supports it.
# We could do it ourselves, but that's a lot of work and will be slow
# in Python.
#
# The only reason we require scipy is to efficiently solve Cholesky
# systems, L^T L x = y where L is lower-triangular.  numpy can compute
# the Cholesky decomposition L, but has no linear system solver that
# takes advantage of the fact that it is triangular.

def _covariance_factor(A):      return la.cho_factor(A)
def _covariance_solve(L, X):    return la.cho_solve(L, X)
def _covariance_logsqrtdet(L):  M, _low = L; return np.sum(np.log(np.diag(M)))

def logpdf(X, Mu, Sigma):
  """Multivariate normal log pdf."""
  # This is the multivariate normal log pdf for a column X of n
  # outputs, a column Mu of n means, and an n-by-n positive-definite
  # covariance matrix Sigma.  The direct-space density is:
  #
  #     p(X | Mu, Sigma)
  #       = ((2 pi)^n det Sigma)^(-1/2)
  #         exp((-1/2) (X - Mu)^T Sigma^-1 (X - Mu)),
  #
  # Since Sigma is symmetric and positive-definite, it has a Cholesky
  # decomposition
  #
  #     Sigma = L^T L
  #
  # for some lower-triangular matrix L.  We can use this both to
  # compute Sigma^-1 X efficiently, i.e. to solve Sigma alpha = X, and
  # to compute det Sigma efficiently, since
  #
  #     det Sigma = det (L^T L) = (det L^T) (det L) = (det L)^2,
  #
  # where det L is the determinant of a lower-triangular matrix and
  # hence is simply the product of the diagonals.
  #
  # We want this in log-space, so we have
  #
  #     log p(X | Mu, Sigma)
  #     = (-1/2) (X - Mu)^T Sigma^-1 (X - Mu) - log ((2 pi)^n det Sigma)^(1/2)
  #     = (-1/2) (X - Mu)^T Sigma^-1 (X - Mu) - log ((2 pi)^n (det L)^2)^(1/2)
  #     = (-1/2) (X - Mu)^T Sigma^-1 (X - Mu) - log ((2 pi)^(n/2) det L)
  #     = (-1/2) (X - Mu)^T Sigma^-1 (X - Mu) - log (2 pi)^(n/2) - log det L
  #     = (-1/2) (X - Mu)^T Sigma^-1 (X - Mu) - (n/2) log (2 pi) - log det L,
  #
  n = len(X)
  assert Mu.shape in ((n,), (n, 1))
  assert Sigma.shape == (n, n)

  X_ = X - Mu

  # Solve
  #
  #     Sigma alpha = X
  #
  # for alpha and compute
  #
  #     log sqrt(det Sigma).
  #
  # If the covariance matrix is not positive-definite, we may be
  # unable to factor it.  In that case, just try to solve the equation
  # by the standard methods and compute the determinant naively.
  try:
    L = _covariance_factor(Sigma)
  except la.LinAlgError:
    alpha = la.solve(Sigma, X_)
    logsqrtdet = (1/2.)*np.log(la.det(Sigma))
  else:
    alpha = _covariance_solve(L, X_)
    logsqrtdet = _covariance_logsqrtdet(L)

  # Compute the log density.
  logp = -np.dot(X_.T, alpha)/2.
  logp -= (n/2.)*np.log(2*np.pi)
  logp -= logsqrtdet

  # Convert 1x1 matrix to float.
  return float(logp)

def dlogpdf(X, Mu, dMu, Sigma, dSigma):
  """Gradient of multivariate normal logpdf with respect to parameters.

  This does not compute the gradient with respect to the outputs.

  XXX Actually, this does not give the gradient of the logpdf with
  respect to Mu and Sigma -- that is, the linear map from an increment
  in (Mu, Sigma) to an increment in the logpdf.  Instead, it evaluates
  that linear map for a given increment in (Mu, Sigma).  So it's not
  actually very useful, and recorded here only for future reference.

  The reason for this is that it's not clear we have -- in numpy
  generally or in Venture specifically -- any representation A for the
  linear functional of M(n, n) ---> R sending

      H |---> tr ((alpha alpha^T - Sigma^-1) H)

  such that

      H |---> numpy.dot(A, H)

  is the same map, where alpha = Sigma^-1 (X - Mu).  There is no nice
  matrix representation of A because it is itself a linear functional
  on n-by-n matrices, and any matrix is at most a (1,1)-tensor,
  whereas we need a (0, n)-tensor.  Maybe numpy has some fancy tensor
  representation for which numpy.dot will DTRT, but it's not clear.
  """
  # Derivative with respect to Mu, using the matrix calculus identity
  # d/du (u^T A u) = u^T (A + A^T), the chain rule, and symmetry of
  # Sigma and hence of Sigma^-1 too:
  #
  #     d/dMu log p(X | Mu, Sigma)
  #       = d/dMu (-1/2) (X - Mu)^T Sigma^-1 (X - Mu)
  #       = (-1/2) (X - Mu)^T (Sigma^-1 + (Sigma^-1)^T) (d/dMu (X - Mu))
  #       = (-1/2) (X - Mu)^T (Sigma^-1 + Sigma^-1) (-I)
  #       = (-1/2) (X - Mu)^T 2 Sigma^-1 (-I)
  #       = (X - Mu)^T Sigma^-1
  #       = ((Sigma^-1)^T (X - Mu))^T
  #       = (Sigma^-1 (X - Mu))^T
  #       = alpha^T,
  #
  # where alpha = Sigma^-1 (X - Mu).
  #
  # Derivative with respect to Sigma, using the matrix calculus
  # identities
  #
  #     (d/dA A^-1) h = -A^-1 h A^-1,
  #     (d/dA log det A) h = tr (A^-1 h):
  #
  #     (d/dSigma log p(X | Mu, Sigma)) h
  #       = (d/dSigma [(-1/2) (X - Mu)^T Sigma^-1 (X - Mu)
  #                     - (n/2) log (2 pi)
  #                     - log (det Sigma)^(1/2)]) h
  #       = (d/dSigma (-1/2) (X - Mu)^T Sigma^-1 (X - Mu)) h
  #         - (d/dSigma (1/2) log det Sigma) h
  #       = (-1/2) (d/dSigma (X - Mu)^T Sigma^-1 (X - Mu)) h
  #         - (1/2) (d/dSigma log det Sigma) h
  #       = (-1/2) (X - Mu)^T (-Sigma^-1 h Sigma^-1) (X - Mu)
  #         - (1/2) tr (Sigma^-1 h)
  #       = (1/2) (X - Mu)^T Sigma^-1 h Sigma^-1 (X - Mu)
  #         - (1/2) tr (Sigma^-1 h)
  #       = (1/2) (X - Mu)^T (Sigma^-1)^T h Sigma^-1 (X - Mu)
  #         - (1/2) tr (Sigma^-1 h)
  #       = (1/2) (Sigma^-1 (X - Mu))^T h Sigma^-1 (X - Mu)
  #         - (1/2) tr (Sigma^-1 h)
  #       = (1/2) alpha^T h alpha - (1/2) tr (Sigma^-1 h)
  #       = (1/2) tr (alpha^T h alpha) - (1/2) tr (Sigma^-1 h)
  #       = (1/2) tr (alpha alpha^T h) - (1/2) tr (Sigma^-1 h)
  #       = (1/2) tr (alpha alpha^T h - Sigma^-1 h)
  #       = (1/2) tr ((alpha alpha^T - Sigma^-1) h).
  #
  # We can efficiently evaluate the trace of a product by the sum of
  # the elements of the Hadamard product, i.e. elementwise product of
  # the matrices, since alpha alpha^T - Sigma^-1 is symmetric.
  #
  n = len(X)
  assert Mu.shape in ((n,), (n, 1))
  assert all(dmu_i.shape == (n,) for dmu_i in dMu)
  assert Sigma.shape == (n, n)
  assert all(dsigma_i.shape == (n, n) for dsigma_i in dSigma)

  # Solve Sigma alpha = (X - Mu), Sigma Sigma^-1 = I.
  #
  # XXX It is ~10 times faster to compute Sigma^-1 and do a single
  # multiplication per partial derivative than to solve a linear
  # system per partial derivative.  But is it numerically safe?  I
  # doubt it.
  try:
    L = _covariance_factor(Sigma)
  except la.LinAlgError:
    alpha = la.solve(Sigma, X - Mu)
    Sigma_inv = np.invert(Sigma)
  else:
    alpha = _covariance_solve(L, X - Mu)
    Sigma_inv = _covariance_solve(L, np.eye(n))

  # Compute Q = alpha alpha^T - Sigma^-1.
  Q = np.dot(alpha, alpha.T) - Sigma_inv

  dlogp_dMu = np.dot(alpha.T, dMu)
  dlogp_dSigma = numpy.array([np.sum(Q*dsigma_i)/2. for dsigma_i in dSigma])

  return (dlogp_dMu, dlogp_dSigma)
