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
# covariance matrices better than LU decomposition.  Problem: neither
# numpy nor scipy supports it.  We could do it ourselves, but that's a
# lot of work and will be slow in Python.

def _covariance_factor(Sigma):
  # Assume it is positive-definite and try Cholesky decomposition.
  try:
    return Covariance_Cholesky(Sigma)
  except la.LinAlgError:
    pass

  # Assume it is at least nonsingular and try LU decomposition.
  try:
    return Covariance_LU(Sigma)
  except la.LinAlgError:
    pass

  # Otherwise, fall back to whatever heuristics scipy can manage.
  return Covariance_Loser(Sigma)

class Covariance_Cholesky(object):
  def __init__(self, Sigma):
    self._cholesky = la.cho_factor(Sigma)
  def solve(self, Y):
    return la.cho_solve(self._cholesky, Y)
  def inverse(self):
    return self.solve(np.eye(self._cholesky[0].shape[0]))
  def logsqrtdet(self):
    # Sigma = L^T L -- but be careful: only the lower triangle and
    # diagonal of L are actually initialized; the upper triangle is
    # garbage.
    L, _lower = self._cholesky

    # det Sigma = det L^T L = det L^T det L = (det L)^2.  Since L is
    # triangular, its determinant is the product of its diagonal.  To
    # compute log sqrt(det Sigma) = log det L, we sum the logs of its
    # diagonal.
    return np.sum(np.log(np.diag(L)))

class Covariance_LU(object):
  def __init__(self, Sigma):
    self._lu = la.lu_factor(Sigma)
    LU, P = self._lu
    # If the sign of the determinant is negative, can't do it.
    signP = +1 if (np.sum(P != np.arange(len(P))) % 2) == 0 else -1
    signU = np.prod(np.sign(np.diag(LU)))
    if signP*signU != +1:
      raise la.LinAlgError('non-positive-semidefinite covariance matrix')
  def solve(self, Y):
    return la.lu_solve(self._lu, Y)
  def inverse(self):
    return self.solve(np.eye(self._lu[0].shape[0]))
  def logsqrtdet(self):
    # P Sigma = L U, where P is a permutation matrix, L is unit lower
    # triangular, and U is upper triangular.  LU stores the lower
    # triangle of L, the diagonal of U, and the upper triangle of U,
    # since the diagonal entries of L are all 1.
    LU, P = self._lu
    diagU = np.diag(LU)

    # Since P is a permutation matrix, L is a unit triangular matrix
    # whose determinant is 1, and U is a triangular matrix whose
    # determinant is the product of its diagonal, we have
    #
    #   det Sigma = det (P L U) = det P * det L * det U
    #     = sign P * 1 * \prod_i u_ii
    #     = sign P \prod_i u_ii.
    #
    # where u_ii is the ith diagonal entry of u.  Since we assume a
    # positive semidefinite covariance matrix, the result is positive,
    # so we can compute this by \sum_i \log_i |u_ii|.  Hence:
    #
    #   log sqrt(det Sigma) = log (\prod_i u_ii)^(1/2)
    #     = (1/2) log \prod_i u_ii
    #     = (1/2) \sum_i \log |u_ii|.
    return (1/2.) * np.sum(np.log(np.abs(diagU)))

class Covariance_Loser(object):
  def __init__(self, Sigma):
    self._Sigma = Sigma
  def solve(self, Y):
    X, _residues, _rank, _sv = la.lstsq(self._Sigma, Y)
    return X
  def inverse(self):
    return la.pinv(self._Sigma)
  def logsqrtdet(self):
    return la.det(self._Sigma)

def logpdf(X, Mu, Sigma):
  """Multivariate normal log pdf."""
  # This is the multivariate normal log pdf for an array X of n
  # outputs, an array Mu of n means, and an n-by-n positive-definite
  # covariance matrix Sigma.  The direct-space density is:
  #
  #     p(X | Mu, Sigma)
  #       = ((2 pi)^n det Sigma)^(-1/2)
  #         exp((-1/2) (X - Mu)^T Sigma^-1 (X - Mu)),
  #
  # We want this in log-space, so we have
  #
  #     log p(X | Mu, Sigma)
  #     = (-1/2) (X - Mu)^T Sigma^-1 (X - Mu) - log ((2 pi)^n det Sigma)^(1/2)
  #     = (-1/2) (X - Mu)^T Sigma^-1 (X - Mu)
  #         - (n/2) log (2 pi) - log sqrt(det Sigma).
  #
  n = len(X)
  assert Mu.shape == (n,)
  assert Sigma.shape == (n, n)

  X_ = X - Mu
  covf = _covariance_factor(Sigma)

  alpha = covf.solve(X_)
  logp = -np.dot(X_.T, covf.solve(X_)/2.)
  logp -= (n/2.)*np.log(2*np.pi)
  logp -= covf.logsqrtdet()

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
  assert Mu.shape == (n,)
  assert all(dmu_i.shape == (n,) for dmu_i in dMu)
  assert Sigma.shape == (n, n)
  assert all(dsigma_i.shape == (n, n) for dsigma_i in dSigma)

  X_ = X - Mu
  covf = _covariance_factor(Sigma)

  # Solve Sigma alpha = X - Mu for alpha.
  #
  # XXX It is ~10 times faster to compute Sigma^-1 and do a single
  # multiplication per partial derivative than to solve a linear
  # system per partial derivative.  But is it numerically safe?  I
  # doubt it.
  alpha = covf.solve(X - Mu)

  # Compute Q = alpha alpha^T - Sigma^-1.
  Q = np.outer(alpha, alpha) - covf.inverse()

  dlogp_dMu = numpy.array([np.dot(alpha, dmu_i) for dmu_i in dMu])
  dlogp_dSigma = numpy.array([np.sum(Q*dsigma_i)/2. for dsigma_i in dSigma])

  return (dlogp_dMu, dlogp_dSigma)

def conditional(X2, Mu1, Mu2, Sigma11, Sigma12, Sigma21, Sigma22):
  """Parameters of conditional multivariate normal."""
  # The conditional distribution of a multivariate normal given some
  # fixed values of some variables is itself a multivariate normal on
  # the remaining values, with a slightly different mean and
  # covariance matrix.  In particular, for
  #
  #     Mu = [Mu_1; Mu_2],
  #     Sigma = [Sigma_11, Sigma_12; Sigma_21, Sigma_22],
  #
  # where `;' separates rows and `,' separates columns within a row,
  # the conditional distribution given the fixed values X_2 for the
  # first block of variables is multivariate normal with
  #
  #     Mu' = Mu_1 + Sigma_12 Sigma_22^-1 (X_2 - Mu_2),
  #     Sigma' = Sigma_11 - Sigma_12 Sigma_22^-1 Sigma_21,
  #
  # where Sigma' is the Schur complement of Sigma_22 in Sigma.
  #
  d1 = len(Mu1)
  d2 = len(Mu2)
  assert X2.shape == (d2,)
  assert Mu1.shape == (d1,)
  assert Mu2.shape == (d2,)
  assert Sigma11.shape == (d1, d1)
  assert Sigma12.shape == (d1, d2)
  assert Sigma21.shape == (d2, d1)
  assert Sigma22.shape == (d2, d2)

  covf22 = _covariance_factor(Sigma22)
  Mu_ = Mu1 + np.dot(Sigma12, covf22.solve(X2 - Mu2))
  Sigma_ = Sigma11 - np.dot(Sigma12, covf22.solve(Sigma21))
  return (Mu_, Sigma_)
