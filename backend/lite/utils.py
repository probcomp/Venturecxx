import random
import numpy.random as npr
import math
import scipy.special
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
  p = ps[os.index(val)]
  assert os.count(val) == 1
  return math.log(p)


def logDensityDirichlet(x, theta):
  xvec = np.array([0.0 for i in theta])
  xvec[x] = 1
  return scipy.special.gammaln(sum(alpha)) - sum(scipy.special.gammaln(alpha)) + np.dot((alpha - 1).T, np.log(xvec).T)
