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
r'''
Smoke Tests
************************
Smoke tests for GP covariance functions
==========================
The test functions do not take any input. We fix both, data vectors and hyper-parameters. The expected results were computed by hand and with MATLAB.

We are using :math:`\mathbf{x} = [1.3, -2, 0]^T`
and  :math:`\mathbf{y} = [1.3, -3.2]^T` to test both :math:`\mathbf{K}(\mathbf{x},\mathbf{x})` and :math:`\mathbf{K}(\mathbf{x},\mathbf{y})`. The hyper-parameters are defined as follows:

:math:`\sigma = 2.1`

:math:`\ell= 1.8`

:math:`p = 0.9`

:math:`\alpha= 0.8`

:math:`\sigma = 2.1`
'''

import numpy as np


from venture.test.config import broken_in
import venture.lite.covariance as cov
import venture.lite.gp as gp



def apply_cov(f):
  x = [1.3,-2,0]
  y = [1.3,-3.2]
  return f(np.asarray(x),np.asarray(x)),f(np.asarray(x),np.asarray(y))


@broken_in('puma', "Puma does not define the covariance function builtins")
def test_const():
  r'''
  Tests a constant covariance function = 2.1
  '''
  sigma = 2.1
  f  = cov.const(sigma)
  cov_train,cov_test = apply_cov(f)
  expect_cov_train = sigma*np.ones((3,3))
  expect_cov_test = sigma*np.ones((3,2))
  np.testing.assert_almost_equal(cov_train, expect_cov_train)
  np.testing.assert_almost_equal(cov_test, expect_cov_test)

@broken_in('puma', "Puma does not define the covariance function builtins")
def test_delta():
  r'''
  Tests the delta covariance function
  WN :math:`=\delta_{x,x^\prime}`
  '''
  f  = cov.delta(0.00001)
  cov_train,cov_test = apply_cov(f)
  expect_cov_train = np.eye(3)
  expect_cov_test = np.zeros((3,2))
  expect_cov_test[0][0]= 1
  np.testing.assert_almost_equal(cov_train, expect_cov_train)
  np.testing.assert_almost_equal(cov_test, expect_cov_test)

@broken_in('puma', "Puma does not define the covariance function builtins")
def test_squaredExponential():
  r'''
  Tests the squared-exponential covariance
  SE :math:`= \exp{-\frac{(x-x^\prime)^2}{2\ell^2}}`
  '''
  l = 1.8
  f  = cov.se(l)
  cov_train,cov_test = apply_cov(f)
  expect_cov_train = np.array([[ 1.        ,  0.18628118,  0.77043084],
				       [ 0.18628118,  1.        ,  0.53941043],
				       [ 0.77043084,  0.53941043,  1.        ]])

  expect_cov_test =  np.array([[ 1.        ,  0.04394558],
					[ 0.18628118,  0.8007483 ],
					[ 0.77043084,  0.20591837]])
  np.testing.assert_almost_equal(cov_train, expect_cov_train, decimal=4)
  np.testing.assert_almost_equal(cov_test, expect_cov_test, decimal=4)


@broken_in('puma', "Puma does not define the covariance function builtins")
def test_periodic():
  r'''
  Tests the periodic covariance
  PER :math:`=  \exp \bigg( \frac{2 \sin^2 ( \pi (x - x^\prime)/p}{\ell^2} \bigg)`
  '''
  l = 1.8
  p = 0.9
  f  = cov.periodic(l,p)
  # enter this into matlab for each entry: exp((-2 * sin(pi*abs(x-y)/p).^2)/(l^2)) 
  cov_train,cov_test = apply_cov(f)
  expect_cov_train =np.array([[ 1.        ,  0.62941043,  0.54954649],
       [ 0.62941043,  1.        ,  0.77488019],
       [ 0.54954649,  0.77487528,  1.        ]])

  expect_cov_test = np.array([[ 1.        ,  1.        ],
       [ 0.62941043,  0.62941043],
       [ 0.54954649,  0.54954649]])

  np.testing.assert_almost_equal(cov_train, expect_cov_train, decimal=4)
  np.testing.assert_almost_equal(cov_test, expect_cov_test, decimal=4)

@broken_in('puma', "Puma does not define the covariance function builtins")
def test_linear():
  r'''
  Tests the linear covariance
  LIN  :math:`= (x-c, x^\prime-c)`
  '''
  f  = cov.linear(0.5)
  cov_train,cov_test = apply_cov(f)
  expect_cov_train = np.array([[ 0.64, -2 ,  -0.4  ],
			       [-2 ,  6.25  ,  1.25  ],
			       [-0.4 ,  1.25  ,  0.25  ]])

  expect_cov_test = np.array([[ 0.64, -2.96],
			      [-2 ,  9.25 ],
			      [ -0.4  ,  1.85 ]])

  np.testing.assert_almost_equal(cov_train, expect_cov_train, decimal=4)
  np.testing.assert_almost_equal(cov_test, expect_cov_test, decimal=4)


@broken_in('puma', "Puma does not define the covariance function builtins")
def test_application_cov_gp():
  r'''
  Tests if a covariance function is correctly applied to vectore input.
  This is mainly for sanity checking that apply_cov in all of the above
  is doing what it should
  '''
  x = [1.3,-2,0]
  y = [1.3,-3.2]
 
  mean_function = gp.mean_const(0.)
  covariance_function = cov.se(1.8)

  cov_train_matrix, cov_test_matrix = apply_cov(covariance_function)
  
  gp_object = gp.GP(mean_function, covariance_function)
  gp_train_matrix = gp_object.cov_matrix(x,x)
  gp_test_matrix = gp_object.cov_matrix(x,y)
 
  np.testing.assert_almost_equal(cov_train_matrix, gp_train_matrix )
  np.testing.assert_almost_equal(cov_test_matrix, gp_test_matrix )


