import random
import numpy.random as npr
import math
import stats_utils as su
import numpy as np
import numbers

# This one is from http://stackoverflow.com/questions/1167617/in-python-how-do-i-indicate-im-overriding-a-method
def override(interface_class):
  def overrider(method):
    assert method.__name__ in dir(interface_class)
    return method
  return overrider

def extendedLog(x): return math.log(x) if x > 0 else float("-inf")

def normalizeList(seq): 
  denom = sum(seq)
  if denom > 0: return [ float(x)/denom for x in seq]
  else: 
    n = float(len(seq))
    return [1.0/n for x in seq]

def simulateCategorical(ps,os=None):
  if os is None: os = range(len(ps))
  ps = normalizeList(ps)
  return os[npr.multinomial(1,ps).argmax()]

def logDensityCategorical(val,ps,os=None):
  if os is None: os = range(len(ps))
  ps = normalizeList(ps)
  # TODO This should work for Venture Values while the comparison is
  # done by identity and in the absence of observations; do I want to
  # override the Python magic methods for VentureValues?
  p = None
  for i in range(len(os)): 
    if os[i] == val: 
      p = ps[i]
      break
  assert p
  return math.log(p)

def simulateDirichlet(alpha): return npr.dirichlet(alpha)

def logDensityDirichlet(theta, alpha):
  theta = np.array(theta)
  alpha = np.array(alpha)

  return su.C.gammaln(sum(alpha)) - sum(su.C.gammaln(alpha)) + np.dot((alpha - 1).T, np.log(theta).T)

# why not use itertools.prod?
def cartesianProduct(original):
  if len(original) == 0: return []
  elif len(original) == 1: return [[x] for x in original[0]]
  else:
    firstGroup = original[0]
    recursiveProduct = cartesianProduct(original[1:])
    return [ [v] + vs for v in firstGroup for vs in recursiveProduct]

def logaddexp(items):
  "Apparently this was added to scipy in a later version than the one installed on my machine.  Sigh."
  the_max = max(items)
  return the_max + math.log(sum(math.exp(item - the_max) for item in items))

def sampleLogCategorical(logs):
  "Samples from an unnormalized categorical distribution given in logspace."
  the_max = max(logs)
  return simulateCategorical([math.exp(log - the_max) for log in logs])

def numpy_force_number(answer):
  if isinstance(answer, numbers.Number):
    return answer
  else:
    return answer[0,0]

def logDensityNormal(x, mu, sigma):
  return -0.5 * ((x - mu) / sigma)**2 - 0.5 * np.log(2 * math.pi * sigma**2)

def logDensityMVNormal(x, mu, sigma):
  assert(mu.size <= 2)
  if mu.size == 1:
    answer = logDensityNormal(x, mu, sigma)
  else:
    sigma_det = sigma[0,0] * sigma[1,1] - sigma[0,1] * sigma[1,0]
    assert(sigma_det > 0)
    sigma_inv = 1.0/sigma_det * np.array([[sigma[1,1], -sigma[0,1]],
                                          [-sigma[1,0], sigma[0,0]]])
    answer =  -.5*np.dot(np.dot(x-mu, sigma_inv), np.transpose(x-mu)) \
              -.5*len(sigma)*np.log(2 * np.pi)-.5*np.log(sigma_det)
  return numpy_force_number(answer)

def chol2d(a):
  sqrt_a00 = math.sqrt(a[0,0])
  L = np.array([[sqrt_a00, 0.0],
                [a[1,0] / sqrt_a00, math.sqrt(a[1,1] - a[1,0] * a[0,1] / a[0,0])]])
  return L

def MVNormalRnd(mu, sigma):
  import pdb
  pdb.set_trace()
  assert(mu.size <= 2)
  if mu.size == 1:
    return npr.normal(mu, math.sqrt(sigma))
  else:
    L = chol2d(sigma)
    return L.dot(npr.normal(size=2)) + mu

def careful_exp(x):
  try:
    return math.exp(x)
  except OverflowError:
    if x > 0: return float("inf")
    else: return float("-inf")

class FixedRandomness(object):
  """A Python context manager for executing (stochastic) code repeatably
against fixed randomness.

  Caveat: If the underlying code attempts to monkey with the state of
  the random number generator (other than by calling it) that
  monkeying will be suppressed, and not propagated to its caller. """

  def __init__(self):
    self.pyr_state = random.getstate()
    self.numpyr_state = npr.get_state()
    random.jumpahead(random.randint(1,2**31-1))
    npr.seed(random.randint(1,2**31-1))

  def __enter__(self):
    self.cur_pyr_state = random.getstate()
    self.cur_numpyr_state = npr.get_state()
    random.setstate(self.pyr_state)
    npr.set_state(self.numpyr_state)

  def __exit__(self, _type, _value, _backtrace):
    random.setstate(self.cur_pyr_state)
    npr.set_state(self.cur_numpyr_state)
    return False # Do not suppress any thrown exception
