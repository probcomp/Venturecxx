# Copyright (c) 2014 MIT Probabilistic Computing Project.
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

# Compute the gradients of simulates and log densities using Sympy.
# Currently, gradient of simulate for gamma, gradient of log density for student T

import sympy as sy
from sympy.simplify import cse
from sympy import init_printing

init_printing()

def compute_gradient(f, wrt, sub_var, sub_value):
  return cse(f.diff(wrt).simplify().subs(sub_var, sub_value).simplify())

def grad_simulate_gamma_gt1():
  '''
  Compute the gradient of simulate for the gamma function in the case
  where the shape paramter alpha > 1.
  '''
  gamma, alpha, beta, b, c, X, U, V = sy.symbols('gamma alpha beta b c X U V')
  b = alpha - sy.Rational(1,3)
  c = 1 / sy.sqrt(9 * b)
  # express X in terms of the current random realization, gamma
  V = (1 + c * X) ** 3
  # can't write out the function itself, because it's identically gamma.
  f = (1 / beta) * b * V
  X_current = (1 / c) * (((gamma * beta) / b) ** sy.Rational(1,3) - 1)
  gradAlpha = compute_gradient(f, alpha, X, X_current)
  gradBeta = compute_gradient(f, beta, X, X_current)
  return gradAlpha, gradBeta

def grad_simulate_gamma_lt1_small_u():
  '''
  Compute the gradient where alpha < 1 and we take the first branch of the
  of statement in the Numpy code (corresponds to U < 1 - alpha).
  '''
  gamma, alpha, beta, X, U = sy.symbols('gamma alpha beta X U')
  X = U ** (1 / alpha)
  f = (1 / beta) * X
  U_current = (gamma * beta) ** alpha
  gradAlpha = compute_gradient(f, alpha, U, U_current)
  gradBeta = compute_gradient(f, beta, U, U_current)
  return gradAlpha, gradBeta

def grad_simulate_gamma_lt1_big_u():
  '''
  Compute the gradient where alpha > 1 and we take the second branch
  '''
  gamma, alpha, beta, X, Y, U = sy.symbols('gamma alpha beta X Y U')
  Y = -sy.log((1 - U) / alpha)
  X = (1 - alpha + alpha * Y) ** (1 / alpha)
  f = (1 / beta) * X
  U_current = 1 - alpha * sy.exp(-(((gamma * beta) ** alpha + alpha - 1) / alpha))
  gradAlpha = compute_gradient(f, alpha, U, U_current)
  gradBeta = compute_gradient(f, beta, U, U_current)
  return gradAlpha, gradBeta

def grad_simulate_gamma():
  '''
  Use sympy to compute gradient of simulate for gamma distribution.
  The actual simulation function is here:
  https://github.com/numpy/numpy/blob/master/numpy/random/mtrand/distributions.c#L124
  Parameters are named as in the numpy code; the output variable is labeled
  as gamma.
  Running in the ipython qt console; printing the outputs will be pretty.
  '''
  f_gt1 = grad_simulate_gamma_gt1()
  f_lt1_small_u = grad_simulate_gamma_lt1_small_u()
  f_lt1_big_u = grad_simulate_gamma_lt1_big_u()
  return f_gt1, f_lt1_small_u, f_lt1_big_u

def grad_of_log_density_t():
  '''
  Use sympy to get the gradient of log density for student t
  '''
  x, nu, loc, shape = sy.symbols('x nu loc shape')
  logp = (sy.loggamma((nu + 1) / 2) - sy.loggamma(nu / 2) -
          sy.Rational(1, 2) * sy.log(sy.pi * nu) - sy.log(shape) -
          ((nu + 1) / 2) * sy.log(1 + (1 / nu) * ((x - loc) / shape) ** 2))
  gradX = logp.diff(x).simplify()
  # this one's messy, so we'll do it in pieces
  gradNu = cse(logp.diff(nu).simplify())
  gradLoc = logp.diff(loc).simplify()
  gradShape = logp.diff(shape).simplify()
  return gradX, gradNu, gradLoc, gradShape



