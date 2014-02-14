import numpy.random as npr
import math
import scipy.special as ss
import numpy as np

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
  p = ps[os.index(val)]
  assert os.count(val) == 1
  return math.log(p)

def simulateDirichlet(alpha): return npr.dirichlet(alpha)

def logDensityDirichlet(theta, alpha):
  theta = np.array(theta)
  alpha = np.array(alpha)

  return ss.gammaln(sum(alpha)) - sum(ss.gammaln(alpha)) + np.dot((alpha - 1).T, np.log(theta).T)

def cartesianProduct(xs):
  if len(xs) == 0: return []
  elif len(xs) == 1: return xs[0]
  elif len(xs) == 2:
    z = []
    for x in xs[0]:
      for y in xs[1]:
        z.append([x,y])
    return z
  else:
    rest = cartesianProduct(xs[1:])
    oneForEach = [[[u] + v for v in rest] for u in xs[0]]
    return [item for sublist in oneForEach for item in sublist]
  
