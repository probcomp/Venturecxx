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
Smoke tests for gradients covariande functions
==========================
The test functions do not take any input. We fix both, data vectors and other
hyper-parameters to test the gradients.

We are using :math:`\mathbf{x} = [1.3, -2, 0]^T` for vector input and math:`x =
1.3 and x\^prime=-2` for scalar input to compute the partial derivatives.
The hyper-parameters are defined as follows:

:math:`\sigma = 2.1`

:math:`\ell= 1.8`

:math:`p = 0.9`

:math:`\alpha= 0.8`

We first assert that the partial derivatives are not NAN, then that they are of
type np.float64.

The partial derivatives for the covariance functions are compared with a value
commputed by hand. The derivations where checked with Wolfram alpha and seem to
be correct.

'''

import os
import sys
import inspect
import numpy as np


from venture.test.config import in_backend
import venture.lite.covariance as covs



CURRENTDIR = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
PARENTDIR = os.path.dirname(CURRENTDIR)
sys.path.insert(0, PARENTDIR)


def apply_cov_scalar(covariance_function):
    """ compute any covariance function with a given scalar"""
    x_1 = np.array([[1.3]]).T
    x_2 = np.array([[-2]]).T
    return covariance_function(x_1, x_2)

@in_backend("lite")
def test_se_gradient():
    r'''
    Tests the gradient for the se covariance
    SE :math:`=  \exp{-\frac{(x-x^\prime)^2}{2\ell^2}}`
    '''
    #df/dsigma
    # TODO - remove this pylint disable once gradients are in place.
    # pylint: disable=no-member
    gp_kernel = covs.se(1.8)
    dfdl = gp_kernel.df[0]
    #(exp((-(1.3+2)^2)/(2*1.8*1.8)) * (1.3+2)^2 )/(1.8^3) = 0.347819847336756
    expected_l = 0.347819847336756

    computed_d_l = apply_cov_scalar(dfdl)

    # TODO - no idea why pylint claims that "Module 'numpy' has no 'isnan'
    # member" - maybe a problem with python versions?
    # pylint: disable=no-member
    assert not np.isnan(computed_d_l)
    assert  computed_d_l.dtype.type is np.float64, """ computed partial derivative
    for l is not of type np.float64"""

    np.testing.assert_almost_equal(computed_d_l, expected_l)

@in_backend("lite")
def test_lin_gradient():
    r'''
    Tests the gradient for the linear covariance function
    LIN  :math:`=(x - \sigma)  (x^\prime - \sigma)`
    '''
    #df/dsigma
    # TODO - remove this pylint disable once gradients are in place.
    # pylint: disable=no-member
    gp_kernel = covs.linear(2.1)
    dfdsigma = gp_kernel.df[0]

    # 2  * 2.1 - 1.3 + 2.0  = 4.9
    expected_sigma = 4.9
    computed_d_sigma = apply_cov_scalar(dfdsigma)

    # TODO - no idea why pylint claims that "Module 'numpy' has no 'isnan'
    # member" - maybe a problem with python versions?
    # pylint: disable=no-member
    assert not np.isnan(computed_d_sigma)

    assert  computed_d_sigma.dtype.type is np.float64, """ computed partial derivative
    for sigma is not of type np.float64"""

    np.testing.assert_almost_equal(computed_d_sigma, expected_sigma)



@in_backend("lite")
def test_const_gradient():
    r'''
    Tests the gradient of the noise covariance
    WN :math:`=\sigma^2 \delta_{x,x^\prime}`
    '''

    #df/dsigma
    # TODO - remove this pylint disable once gradients are in place.
    # pylint: disable=no-member
    gp_kernel = covs.makeConst(2.1)
    dfdsigma = gp_kernel.df[0]
    expected = 2 * 2.1

    computed_d_sigma = apply_cov_scalar(dfdsigma)

    # TODO - no idea why pylint claims that "Module 'numpy' has no 'isnan'
    # member" - maybe a problem with python versions?
    # pylint: disable=no-member
    assert not np.isnan(computed_d_sigma)

    assert  computed_d_sigma.dtype.type is np.float64, """ computed partial derivative
    for sigma is not of type np.float64"""

    np.testing.assert_almost_equal(computed_d_sigma, expected)


