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

import numpy as np
from numpy.linalg import solve
from scipy.optimize import minimize
from functools import partial

def bivariate_normal_contour(ax, mu, Sigma, **kwargs):
    '''
    Draws the 2-std contour of a bivariate Gaussian onto a set of axes.
    Useful to, for instance, visually evaluate behaviors of different samplers.

    Parameters
    ----------
    ax : The axes onto which to draw the contour
    mu : The mean vector
    sigma : The covariance matrix

    Additional arguments passed to the contour function
    '''
    mu = mu.astype(np.float)
    Sigma = Sigma.astype(np.float)
    mu0 = mu[0]
    mu1 = mu[1]
    # get the "height" of the density at 1 conditional standard deviation
    sigma_bar = np.sqrt(Sigma[0,0] - (Sigma[0,1] * Sigma[1,0]) / Sigma[1,1])
    h = mahalanobis(2 * sigma_bar, 0, np.array([0,0]), Sigma)
    # compute the plot scale
    xdist, ydist = compute_scale(Sigma, h)
    # draw the level curves
    x0 = np.linspace(mu0 - xdist, mu0 + xdist, 100)
    x1 = np.linspace(mu1 - ydist, mu1 + ydist, 100)
    X0, X1 = np.meshgrid(x0, x1)
    Y = this_mahalanobis(mu, Sigma)(X0, X1)
    ax.contour(X0, X1, Y, [h], **kwargs)

def this_mahalanobis(mu, Sigma):
    return np.vectorize(partial(mahalanobis, mu = mu, Sigma = Sigma))

def mahalanobis(x0, x1, mu, Sigma):
    'The mahalanobis distance'
    x = np.array([x0, x1])
    x_centered = x - mu
    return np.sqrt(np.dot(x_centered, solve(Sigma, x_centered)))

def compute_scale(Sigma, h):
    'Figure out the scale for the plot'
    m = partial(mahalanobis, mu = np.array([0,0]), Sigma = Sigma)
    cons = ({'type' : 'eq', 'fun' : lambda x: m(x[0], x[1]) - h})
    xdist = minimize(fun = lambda x: x[0], x0 = np.array([np.sqrt(Sigma[0,0]), 0]),
                     constraints = cons, method = 'SLSQP').x[0]
    ydist = minimize(fun = lambda x: x[1], x0 = np.array([0, np.sqrt(Sigma[1,1])]),
                     constraints = cons, method = 'SLSQP').x[1]
    return 1.1 * np.abs(xdist), 1.1 * np.abs(ydist)
