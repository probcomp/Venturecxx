'''
Illustrates sequential Bayesian updating in Venture, for linear regression
model in 2 dimensions
'''

from __future__ import division
from venture.unit import Analytics, MRipl
import numpy as np, scipy as sp, pandas as pd
from matplotlib import pyplot as plt
from numpy import matrix
from numpy.linalg import inv, det
from scipy.special import gamma
from venture.shortcuts import (make_puma_church_prime_ripl,
                               make_lite_church_prime_ripl)

def make_data():
  w = matrix([0.5, -0.25]).T
  sigma_2 = 0.25
  X = matrix(np.random.uniform(-1, 1, size = [20,2]))
  y = matrix(np.random.normal(X * w, np.sqrt(sigma_2)))
  return {'X' : X, 'y' : y, 'w' : w, 'sigma_2' : sigma_2}

def build_ripl():
  # r = MRipl(backend = 'lite', no_ripls = 1, local_mode = False)
  r = make_lite_church_prime_ripl()
  r.load_prelude()
  r.assume('sigma_2', '(inv_gamma 1 1)')
  r.assume('w', '(multivariate_normal (vector 0 0) (matrix (list (vector sigma_2 0) (vector 0 sigma_2))))')
  r.assume('y', '(lambda (x) (normal (dot x w) (sqrt sigma_2)))')
  return r

def build_ripl_scalar():
  r = make_lite_church_prime_ripl()
  r.load_prelude()
  r.assume('sigma_2', '(inv_gamma 1 1)')
  r.assume('w1', '(normal 0 1)')
  r.assume('w2', '(normal 0 1)')
  r.assume('w', '(vector w1 w2)')
  r.assume('y', '(lambda (x) (normal (dot x w) (sqrt sigma_2)))')
  # r.assume('y', '(lambda (x1 x2) (normal (+ (* x1 w1) (* x2 w2)) (sqrt sigma_2)))')
  return r

def initial_belief():
  belief = {}
  belief['w'] = matrix([0,0]).T
  belief['a'] = 1
  belief['b'] = 1
  belief['V'] = matrix([[1,0], [0,1]])
  return belief

def update_belief(X, y, old_belief):
  a_0, b_0, w_0, V_0 = old_belief['a'], old_belief['b'], old_belief['w'], old_belief['V']
  V_N = inv(inv(V_0) + X.T * X)
  w_N = V_N * (inv(V_0) * w_0 + X.T * y)
  n = X.shape[0]
  a_N = a_0 + (n / 2)
  b_N = b_0 + (1 / 2) * (w_0.T * inv(V_0) * w_0 + y.T * y - w_N.T * inv(V_N) * w_N)
  b_N = float(b_N)
  return {'a' : a_N, 'b' : b_N, 'V' : V_N, 'w' : w_N}

def multivariate_t_density(x1, x2, mu, Sigma, nu):
  x = matrix([x1, x2]).T
  D = len(mu)
  V = nu * Sigma
  res = ((gamma(nu / 2 + D / 2) / gamma(nu / 2)) *
         pow(det(np.pi * V), -1/2) *
         pow(int(1 + (x - mu).T * inv(V) * (x - mu)),
                -(nu + D) / 2))
  return res

def plot_belief(belief):
  mu = belief['w']
  Sigma = (belief['b'] / belief['a']) * belief['V']
  nu = 2 * belief['a']
  t = np.r_[-2:2.05:0.05]
  x1grid, x2grid = np.meshgrid(t, t)
  res = []
  for x1, x2 in zip(x1grid.ravel(), x2grid.ravel()):
    res.append(multivariate_t_density(x1, x2, mu, Sigma, nu))
  res = np.array(res).reshape(x1grid.shape)
  plt.contour(x1grid, x2grid, np.log(res), 10)

def runme():
  data = make_data()
  belief = initial_belief()
  new_belief = update_belief(data['X'][0], data['y'][0], belief)
  plot_belief(new_belief)
  new_belief = update_belief(data['X'][2:], data['y'][2:], belief)


