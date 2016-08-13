# Copyright (c) 2013, 2014, 2015 MIT Probabilistic Computing Project.
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

import math
import numbers

import numpy as np
import numpy.linalg as npla
import scipy.special as ss

# This one is from http://stackoverflow.com/questions/1167617/in-python-how-do-i-indicate-im-overriding-a-method
def override(interface_class):
  def overrider(method):
    assert method.__name__ in dir(interface_class)
    return method
  return overrider

def extendedLog(x): return float('-inf') if x == 0 else math.log(x)
def extendedLog1p(x): return float('-inf') if x == -1 else math.log1p(x)
def xlogx(x): return 0 if x == 0 else x*math.log(x)
def expm1(x): return math.expm1(x)

def logsumexp(array):
  """Given [log x_0, ..., log x_{n-1}], yield log (x_0 + ... + x_{n-1}).

  Computed carefully to avoid overflow by computing x_i/max{x_i}
  instead of x_i directly, and to propagate infinities and NaNs
  appropriately.
  """
  if len(array) == 0:
    return float('-inf')
  m = max(array)

  # m = +inf means addends are all +inf, hence so are sum and log.
  # m = -inf means addends are all zero, hence so is sum, and log is
  # -inf.  But if +inf and -inf are among the inputs, or if input is
  # NaN, let the usual computation yield a NaN.
  if math.isinf(m) and min(array) != -m and \
     all(not math.isnan(a) for a in array):
    return m

  # Since m = max{a_0, a_1, ...}, it follows that a <= m for all a,
  # so a - m <= 0; hence exp(a - m) is guaranteed not to overflow.
  return m + extendedLog(sum(careful_exp(a - m) for a in array))

def normalizeList(seq):
  denom = sum(seq)
  if denom > 0: return [ float(x)/denom for x in seq]
  else:
    # Treat all impossible options as equally impossible.
    n = float(len(seq))
    return [1.0/n for x in seq]

def simulateCategorical(ps,np_rng,os=None):
  if os is None: os = range(len(ps))
  ps = normalizeList(ps)
  return os[np_rng.multinomial(1,ps).argmax()]

def logDensityCategorical(val,ps,os=None):
  if os is None: os = range(len(ps))
  ps = normalizeList(ps)
  # TODO This should work for Venture Values while the comparison is
  # done by identity and in the absence of observations; do I want to
  # override the Python magic methods for VentureValues?
  p = 0
  for (pi, oi) in zip(ps, os):
    if oi == val:
      p += pi
  if p == 0:
    return float('-inf')
  return math.log(p)

def logDensityCategoricalSequence(weights, counts):
  """The log probability that repeated application of a categorical with
  the given weights will give a sequence of results described by the
  given counts (all such sequences have the same probability).

  weight-count alignment is positional, abstracting away from any
  underlying objects.  In particular, any collapsing on equal objects
  should be done before calling this.
  """
  def term(w, c):
    if c == 0: return 0 # Even if w == 0
    if w == 0: return float('-inf')
    return np.log(w) * c
  return sum(term(w, c) for (w, c) in zip(weights, counts))

def simulateDirichlet(alpha, np_rng): return np_rng.dirichlet(alpha)

def logDensityDirichlet(theta, alpha):
  theta = np.array(theta)
  alpha = np.array(alpha)

  return ss.gammaln(sum(alpha)) - sum(ss.gammaln(alpha)) + np.dot((alpha - 1).T, np.log(theta).T)

# CONSIDER why not use itertools.prod?
def cartesianProduct(original):
  if len(original) == 0: return [[]]
  elif len(original) == 1: return [[x] for x in original[0]]
  else:
    firstGroup = original[0]
    recursiveProduct = cartesianProduct(original[1:])
    return [ [v] + vs for v in firstGroup for vs in recursiveProduct]

def logaddexp(items):
  "Apparently this was added to scipy in a later version than the one installed on my machine.  Sigh."
  the_max = max(items)
  if the_max > float("-inf"):
    return the_max + math.log(sum(math.exp(item - the_max) for item in items))
  else:
    return the_max # Don't want NaNs from trying to correct from the maximum

def log_domain_even_out(items, n=None):
  "Return a list of n equal numbers whose logsumexp equals the logsumexp of the inputs."
  if n is None:
    n = len(items)
  answer = logaddexp(items) - math.log(n)
  return [answer for _ in range(n)]

def logWeightsToNormalizedDirect(logs):
  "Converts an unnormalized categorical distribution given in logspace to a normalized one given in direct space"
  the_max = max(logs)
  if the_max > float("-inf"):
    # Even if the logs include some -inf values, math.exp will produce
    # zeros there and it will be fine.
    return normalizeList([math.exp(log - the_max) for log in logs])
  else:
    # If all the logs are -inf, force 0 instead of NaN.
    return [0 for _ in logs]

def sampleLogCategorical(logs, np_rng):
  "Samples from an unnormalized categorical distribution given in logspace."
  the_max = max(logs)
  if the_max > float("-inf"):
    return simulateCategorical([math.exp(log - the_max) for log in logs],
      np_rng, os=None)
  else:
    # normalizeList, as written above, will actually do the right
    # thing with this, namely treat all impossible options as equally
    # impossible.
    return simulateCategorical([0 for _ in logs], np_rng, os=None)

def numpy_force_number(answer):
  if isinstance(answer, numbers.Number):
    return answer
  else:
    return answer[0,0]

# TODO Change it to use the scipy function when Venture moves to requiring scipy 0.14+
def logDensityMVNormal(x, mu, sigma):
  answer =  -.5*np.dot(np.dot(x-mu, npla.inv(sigma)), np.transpose(x-mu)) \
            -.5*len(sigma)*np.log(2 * np.pi)-.5*np.log(abs(npla.det(sigma)))
  return numpy_force_number(answer)

def careful_exp(x):
  try:
    return math.exp(x)
  except OverflowError:
    return float("inf")

def logistic(x):
  """Logistic function: 1/(1 + e^{-x}).  Inverse of logit.

  Maps log-odds space probabilities into direct-space in [0, 1].
  """
  # logistic never overflows, but e^{-x} does if x is much less than
  # -log 2^(emax + 1) ~= -709.  Fortunately, for x <= -37, IEEE 754
  # double-precision arithmetic rounds 1 + e^{-x} to e^{-x} anyway,
  # giving the approximation 1/(1 + e^{-x}) ~= 1/e^{-x} = e^x, which
  # never overflows.
  #
  if x <= -37:
    return np.exp(x)
  else:
    return 1/(1 + np.exp(-x))

def T_logistic(x):
  """Tangent vector of logistic function: (logistic(x), d/dx logistic(x))."""
  # If L is the logistic function, we have
  #
  #                 e^{-x}         e^{-x}         1
  #     L'(x) = -------------- = ---------- * ----------
  #             (1 + e^{-x})^2   1 + e^{-x}   1 + e^{-x}
  #
  #                e^{-x}*e^x          1
  #           = ---------------- * ----------
  #             (1 + e^{-x})*e^x   1 + e^{-x}
  #
  #                1           1
  #           = ------- * ----------
  #             e^x + 1   1 + e^{-x}
  #
  #           = L(-x) L(x) = (1 - L(x)) L(x).
  #
  # We could compute L'(x) by computing L(x) and then multiplying L(x)
  # and 1 - L(x), but that would lose precision for both factors if
  # either one were near 1.  We could compute L(x) and L(-x)
  # separately, but that would cost two exps.  We instead compute L(x)
  # and L'(x) simultaneously in terms of e^{-x}.
  #
  if x <= -37:
    # When x <= -37, so that 1 + e^{-x} ~= e^{-x}, we have
    #
    #   1/(1 + e^{-x}) = 1/e^{-x} = e^x
    #   e^{-x}/(1 + e^{-x})^2 = e^{-x}/e^{-x}^2 = 1/e^{-x} = e^x.
    #
    ex = np.exp(x)
    return (ex, ex)
  else:
    ex = np.exp(-x)
    ex1 = 1 + ex
    return (1/ex1, ex/(ex1*ex1))

def d_logistic(x):
  """d/dx logistic(x) = e^{-x} / (1 + e^{-x})^2"""
  if x <= -37:
    # 1 + e^{-x} ~= e^{-x}, so e^{-x} / (1 + e^{-x}) ~=
    # e^{-x}/(e^{-x})^2 = 1/e^{-x} = e^x.
    return np.exp(x)
  else:
    ex = np.exp(-x)
    ex1 = 1 + ex
    return ex/(ex1*ex1)

def log_d_logistic(x):
  """log d/dx logistic(x) = -x - 2 log (1 + e^{-x})"""
  if x <= -37:
    # -x - 2 log (1 + e^{-x}) ~= -x - 2 log (e^{-x}) = -x - 2 (-x) = x
    return x
  else:
    return -x - 2*extendedLog1p(careful_exp(-x))

def log_logistic(x):
  """log logistic(x) = log 1/(1 + e^{-x}) = -log1p(e^{-x})

  Maps log-odds space probabilities in \R into log-space in (-\infty, 0].
  """
  if x <= -37:
    return x
  else:
    # log 1/(1 + e^{-x}) = log 1 - log (1 + e^{-x}) = -log1p(e^{-x}).
    #
    # When x is large and positive, e^{-x} is small relative to 1, so
    # computing 1 + e^{-x} may lose precision, which log1p avoids.
    #
    return -np.log1p(np.exp(-x))

def d_log_logistic(x):
  """Derivative of the log-logistic function: d/dx log logistic(x)."""
  # Since 1 - L(x) = L(-x) and L'(x) = L(x) (1 - L(x)) = L(x) L(-x),
  # we have
  #
  #     (log o L)'(x) = L'(x) log'(L(x)) = L(x) L(-x) / L(x) = L(-x).
  #
  return logistic(-x)

def logit(x):
  """Logit function, x/(1 - x).  Inverse of logistic.

  Maps direct-space probabilities in [0, 1] into log-odds space.
  """
  return extendedLog(x / (1 - x))

def simulateLogGamma(shape, np_rng):
  """Sample from log of standard Gamma distribution with given shape."""
  if shape < 1:
    # For shape < 1, if G ~ Gamma(shape + 1) and U ~ U[0, 1], then
    # G * U^(1/shape) ~ Gamma(shape).  See
    #
    #       Luc Devroye, _Nonuniform Random Variate Generation_,
    #       Springer-Verlag, 1986, Ch. IX `Continuous univariate
    #       densities', Sec. 3.5 'Gamma variate generators when a
    #       <= 1', p. 420,
    #
    # in particular option (3), the generator based on Stuart's
    # theorem.  We compute log (G * U^(1/shape)) in log space by
    # log G + (log U)/shape in order to avoid overflow when shape
    # is very small.
    #
    G = np_rng.gamma(shape + 1)
    U = np_rng.uniform()
    return math.log(G) + math.log(U)/shape
  else:
    # Otherwise, if shape >= 1, simply take the log of a Gamma
    # sample.  When shape = 1, the probability of any quantity
    # rounded to zero is less than 1e-300 which is well below
    # 2^-256 which will never happen.  Larger shapes give even
    # smaller probability of yielding zero.
    #
    return math.log(np_rng.gamma(shape))

def logDensityLogGamma(x, shape):
  """Log density of the log of a Gamma sample with given shape."""
  # For shape k, the Gamma PDF is
  #
  #     Gamma(y; k) = y^{k - 1} e^-y / Gamma(k),   or
  #     log Gamma(y; k) = (k - 1) log y - y - log Gamma(k);
  #
  # hence if x = log y and thus y = e^x so dy/dx = d/dx e^x = e^x, we
  # have
  #
  #     log LogGamma(x; k) = log [Gamma(y; k) dy/dx]
  #       = (k - 1) log y - y - log Gamma(k) + log dy/dx
  #       = (k - 1) log e^x - e^x - log Gamma(k) + log e^x
  #       = (k - 1) x - e^x - log Gamma(k) + x
  #       = k x - e^x - log Gamma(k).
  #
  return shape*x - careful_exp(x) - math.lgamma(shape)

class FixedRandomness(object):
  """A Python context manager for executing (stochastic) code repeatably
against fixed randomness.

  Caveat: If the underlying code attempts to monkey with the state of
  the random number generator (other than by calling it) that
  monkeying will be suppressed, and not propagated to its caller. """

  def __init__(self, py_rng, np_rng):
    self.py_rng = py_rng
    self.np_rng = np_rng
    self.pyr_state = py_rng.getstate()
    self.numpyr_state = np_rng.get_state()
    py_rng.jumpahead(py_rng.randint(1,2**31-1))
    np_rng.seed(py_rng.randint(1,2**31-1))

  def __enter__(self):
    self.cur_pyr_state = self.py_rng.getstate()
    self.cur_numpyr_state = self.np_rng.get_state()
    self.py_rng.setstate(self.pyr_state)
    self.np_rng.set_state(self.numpyr_state)

  def __exit__(self, _type, _value, _backtrace):
    self.py_rng.setstate(self.cur_pyr_state)
    self.np_rng.set_state(self.cur_numpyr_state)
    return False # Do not suppress any thrown exception

# raise is a statement and can't be used in a lambda :(
def raise_(e): raise e
