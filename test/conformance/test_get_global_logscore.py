# Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
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

from __future__ import division

import math

from nose.tools import assert_almost_equal
from scipy import stats

from venture.lite import types as t
from venture.lite.psp import LikelihoodFreePSP
from venture.lite.sp_help import typed_nr
from venture.test.config import get_ripl
from venture.test.config import on_inf_prim

@on_inf_prim("none")
def test_global_logscore():
    ripl = get_ripl()
    for _ in range(100):
        ripl.observe('(flip (exactly 0.5))', 'true')
    ripl.infer('(incorporate)')
    logscore = ripl.get_global_logscore()[0]
    logscore_true = -100*math.log(2)
    assert_almost_equal(logscore, logscore_true)

@on_inf_prim("none")
def test_global_logscore_coupled():
    ripl = get_ripl()
    ripl.assume('f', '(exactly (make_beta_bernoulli 1.0 1.0))')
    for _ in range(100):
        ripl.observe('(f)', 'true')
    ripl.infer('(incorporate)')
    logscore = ripl.get_global_logscore()[0]
    logscore_true = -math.log(101)
    assert_almost_equal(logscore, logscore_true)

@on_inf_prim("none")
def test_logscore_likelihood_free():
    "Shouldn't break in the presence of likelihood-free SP's"
    ripl = setup_likelihood_free()
    for _ in range(100):
        ripl.observe('(flip)', 'true')
    ripl.infer('(incorporate)')
    ripl.predict('(test1 0)')
    ripl.predict('(test2 0)')
    ripl.get_global_logscore()

def setup_likelihood_free():
    class TestPSP1(LikelihoodFreePSP):
        def simulate(self, args):
            x = args.operandValues()[0]
            return x + stats.distributions.norm.rvs()
    tester1 = typed_nr(TestPSP1(), [t.NumberType()], t.NumberType())

    class TestPSP2(LikelihoodFreePSP):
        def simulate(self, args):
            x = args.operandValues()[0]
            return x + stats.distributions.bernoulli(0.5).rvs()
    tester2 = typed_nr(TestPSP2(), [t.NumberType()], t.NumberType())
    ripl = get_ripl()
    ripl.bind_foreign_sp('test1', tester1)
    ripl.bind_foreign_sp('test2', tester2)
    return ripl

def test_loglikelihood_logjoint():
    exp = math.exp
    lgamma = math.lgamma
    log = math.log
    log1p = math.log1p

    # Exponential: p(alpha) = e^{-alpha}
    alpha = -log(1/2)
    logp_alpha = -alpha
    assert_almost_equal(logp_alpha, -0.6931472)

    # Beta: p(theta | alpha) = Beta(theta; alpha, alpha)
    #   = theta^{alpha - 1} (1 - theta)^{alpha - 1} / Beta(alpha, alpha)
    #   = (theta*(1 - theta))^{alpha - 1} Gamma(2*alpha) / Gamma(alpha)^2
    theta = 3/4
    logp_theta_given_alpha = (alpha - 1)*(log(theta) + log1p(-theta)) \
        + lgamma(2*alpha) - 2*lgamma(alpha)
    assert_almost_equal(logp_theta_given_alpha, -0.1436)

    # Bernoulli: p(x_i | theta) = theta delta_xi + (1 - theta) delta_{1 - xi}
    x_0 = 0
    x_1 = 1
    logp_x_given_theta = log(theta) + log1p(-theta)
    assert_almost_equal(logp_x_given_theta, log(3/16))

    def check(expression, value):
        assert_almost_equal(ripl.infer(expression)[0], value)

    # Unconditional model:
    #
    #   alpha ~ Expon(1)
    #   theta ~ Beta(alpha, alpha)
    #   X_i ~ Bernoulli(theta)

    ripl = get_ripl()
    ripl.assume('alpha', '(tag (quote alpha) 0 (expon 1))')
    ripl.force('alpha', alpha)
    ripl.assume('theta', '(tag (quote theta) 0 (beta alpha alpha))')
    ripl.force('theta', theta)
    ripl.observe('(bernoulli theta)', x_0)
    ripl.observe('(bernoulli theta)', x_1)

    # p(theta | alpha)
    check('(log_likelihood_at (quote alpha) 0)', logp_theta_given_alpha)

    # p(x | theta)
    check('(log_likelihood_at (quote theta) 0)', logp_x_given_theta)

    # p(x | theta, alpha) = p(x | theta)
    check('(log_likelihood_at default all)', logp_x_given_theta)

    # p(theta, alpha) = p(theta | alpha) p(alpha)
    check('(log_joint_at (quote alpha) 0)',
          logp_theta_given_alpha + logp_alpha)

    # p(x, theta | alpha) = p(x | theta) p(theta | alpha)
    check('(log_joint_at (quote theta) 0)',
          logp_x_given_theta + logp_theta_given_alpha)

    # p(x, theta, alpha) = p(x | theta) p(theta | alpha) p(alpha)
    check('(log_joint_at default all)',
          logp_x_given_theta + logp_theta_given_alpha + logp_alpha)

    assert_almost_equal(ripl.get_global_logscore()[0], logp_x_given_theta)
    check('global_log_joint',
          logp_x_given_theta + logp_theta_given_alpha + logp_alpha)

    # Conditional model:
    #
    #   alpha ~ Expon(1)
    #   theta ~ Exactly(0.5), if alpha > 2; else Beta(alpha, alpha)
    #   X_i ~ Bernoulli(theta)

    ripl = get_ripl()
    ripl.assume('alpha', '(tag (quote alpha) 0 (expon 1))')
    ripl.force('alpha', alpha)
    ripl.assume('theta', '''
        (tag (quote theta) 0
          (if (> alpha 2) (exactly 0.5) (beta alpha alpha)))
    ''')
    ripl.force('theta', theta)
    ripl.observe('(bernoulli theta)', x_0)
    ripl.observe('(bernoulli theta)', x_1)

    # p(x | theta)      XXX ?
    check('(log_likelihood_at (quote alpha) 0)', logp_x_given_theta)

    # p(x | theta)      XXX ?
    check('(log_likelihood_at (quote theta) 0)', logp_x_given_theta)

    # p(x | theta)      XXX ?
    check('(log_likelihood_at default all)', logp_x_given_theta)

    # likelihood * p(alpha) = p(x | theta) p(alpha)
    check('(log_joint_at (quote alpha) 0)', logp_x_given_theta + logp_alpha)

    # likelihood * p(theta | alpha) = p(x | theta) p(theta | alpha)
    #   = p(x, theta | alpha)
    check('(log_joint_at (quote theta) 0)',
          logp_x_given_theta + logp_theta_given_alpha)

    # likelihood * p(alpha) = p(x | theta) p(theta | alpha) p(alpha)
    #   = p(x, theta, alpha)
    check('(log_joint_at default all)',
          logp_x_given_theta + logp_theta_given_alpha + logp_alpha)

    assert_almost_equal(ripl.get_global_logscore()[0], logp_x_given_theta)
    check('global_log_joint',
          logp_x_given_theta + logp_theta_given_alpha + logp_alpha)
