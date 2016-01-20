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
import scipy.stats as stats
from nose.plugins.attrib import attr
from venture.lite.infer.subsampled_mh import sequentialTest
from venture.test.config import in_backend, get_ripl, collectSamples, broken_in, on_inf_prim
from venture.test.stats import statisticalTest, reportKnownContinuous

@in_backend("none")
def testSequentialTest():
  mu_0 = 0.2
  k0 = 3
  Nbatch = 2
  N = 20
  epsilon = 0.1

  ys = [[-1.37, -2.37, 1.96, -0.27, -2.38, -0.41, -1.69, -0.63, 2.85, 2.98, -1.49, -0.75, 0.85, 0.23, -1.02, 2.04, -2.84, 5.09, -0.72, 0.80],
      [-1.41, -2.04, 2.27, 0.08, 0.46, 0.25, 1.39, 3.48, 1.33, 1.38, 2.48, 1.80, -2.30, -0.53, -3.25, 1.16, 3.80, 3.16, 1.84, -1.88],
      [-1.47, 0.36, -0.26, 1.74, 2.63, -0.50, -0.14, 2.19, 0.98, -3.36, -1.62, -1.50, -2.65, -0.36, 0.26, 2.79, 1.41, 2.33, -1.51, 0.64],
      [3.27, -1.30, 1.35, 2.55, -2.08, 0.98, -1.81, -0.95, -1.33, -1.00, -0.62, -1.67, -1.26, 1.00, 3.34, -3.08, -0.54, 0.68, 0.97, 1.91],
      [0.26, -3.48, 1.34, 1.80, -1.10, -0.64, -1.17, -0.33, -1.87, 2.38, -2.43, -0.76, 2.65, 0.77, -0.72, -0.85, 0.77, 1.81, 1.44, 3.47],
      [-2.02, -0.36, -4.05, 0.82, 1.47, 0.16, -3.37, -4.12, 3.64, -2.50, 1.87, -0.34, -0.16, -1.22, 1.14, -0.31, -2.14, -0.63, -0.03, -0.26],
      [0.89, 0.80, -5.03, -1.58, -0.23, 0.95, 1.37, 1.08, -0.76, 2.89, -1.62, -2.94, 0.85, 1.93, 1.94, 1.04, 1.75, 0.32, 3.13, 2.71],
      [0.19, 1.57, 2.22, 3.00, -0.26, 2.52, 2.19, 1.95, 2.40, -0.21, 1.24, 2.18, -0.88, -2.56, 1.32, 0.40, 0.90, -0.03, -1.69, 0.97],
      [1.87, 0.58, -0.43, -0.08, -0.46, -2.76, 0.53, 2.12, 0.12, -1.13, 1.33, 2.42, 0.91, 0.99, 0.44, -1.15, 0.26, 2.26, -0.11, 1.41],
      [-0.12, 1.18, -1.24, -2.38, -4.87, 1.46, 0.69, 1.46, 1.14, -3.56, 0.21, 3.87, 1.86, -0.30, -0.94, -0.73, 0.52, 0.37, -1.79, -0.91]]

  accepts_expect = map(bool, [0, 1, 0, 0, 0, 0, 1, 1, 1, 0])

  ns_expect = [6, 12, 14, 14, 12, 8, 20, 6, 18, 10]

  tstats_expect = [-1.758886, 2.541570, -1.820940, -1.574872, -2.159024, -2.587167, 0.018556, 2.912594, 2.283297, -1.569315]

  for i in range(len(ys)):
    accept, n, tstat = sequentialTest(mu_0, k0, Nbatch, N, epsilon, lambda j: ys[i][j])
    assert accept == accepts_expect[i]
    assert n == ns_expect[i]
    assert abs(tstat - tstats_expect[i]) < 1e-5

# In the following two tests, the sample distribution is an approximation to
# cdf with the accuracy controlled by epsilon, the fifth argument.
@attr('slow')
@broken_in('puma', "Subsampled MH only implemented in Lite.")
@statisticalTest
@on_inf_prim("subsampled_mh")
def testNormalWithObserves1():
  ripl, post_mean, post_std, cdf = setupNormalWithObserves(100, 3.0)
  predictions = collectSamples(ripl,"pid",infer="(subsampled_mh default one 2 3 0.01 false 0 false 50)")
  return reportKnownContinuous(cdf, predictions, "N(%f,%f^2)" % (post_mean, post_std))

@attr('slow')
@broken_in('puma', "Subsampled MH only implemented in Lite.")
@statisticalTest
@on_inf_prim("subsampled_mh")
def testNormalWithObserves2():
  ripl, post_mean, post_std, cdf = setupNormalWithObserves(100, 3.0)
  # The sample distribution is an approximation to cdf with the accuracy
  # controlled by epsilon, the fifth argument.
  predictions = collectSamples(ripl,"pid",infer="(subsampled_mh default one 2 3 0.01 true %f false 50)" % post_std)
  return reportKnownContinuous(cdf, predictions, "N(%f,%f^2)" % (post_mean, post_std))

def setupNormalWithObserves(N, sigma):
  ripl = get_ripl()
  ripl.assume("mu", "(normal 10.0 %f)" % sigma, label="pid")
  x = np.random.normal(10,1,N)
  for i in range(len(x)):
    ripl.observe("(normal mu 1.0)", x[i])

  sigma2 = sigma**2
  post_mean = (sigma2 * sum(x) + 10.0) / float(sigma2 * N + 1.0)
  post_std = np.sqrt(sigma2 / float(sigma2 * N + 1.0))
  cdf = stats.norm(loc=post_mean, scale=post_std).cdf

  return ripl, post_mean, post_std, cdf
