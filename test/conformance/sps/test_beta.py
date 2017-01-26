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

from __future__ import division

import math
import multiprocessing
import random
import traceback

import nose.tools
import numpy as np
import numpy.random as npr
import scipy.integrate
import scipy.stats

from venture.lite.continuous import BetaOutputPSP
from venture.lite.continuous import LogBetaOutputPSP
from venture.lite.continuous import LogOddsBetaOutputPSP
from venture.lite.continuous import LogOddsUniformOutputPSP
from venture.lite.sp_use import MockArgs
from venture.lite.utils import exp
from venture.lite.utils import logistic

from venture.test.config import broken_in
from venture.test.config import collectSamples
from venture.test.config import default_num_samples
from venture.test.config import get_ripl
from venture.test.config import on_inf_prim
from venture.test.config import stochasticTest
from venture.test.stats import reportKnownContinuous
from venture.test.stats import statisticalTest

# Sane replacement for brain-damaged nose.tools.timed, which waits for
# the test to complete and *then* checks whether it took too long.
def timed(seconds):
    """Decorator for a nose test with a time limit in seconds.

    The time limit is enforced, unlike in nose.tools.timed, which
    waits for the test to complete and *then* checks whether it took
    too long.
    """
    def wrap(f):
        @nose.tools.make_decorator(f)
        def f_(*args, **kwargs):
            (pipe_recv, pipe_send) = multiprocessing.Pipe(duplex=False)
            def f__(*args, **kwargs):
                try:
                    try:
                        pipe_send.send((True, f(*args, **kwargs)))
                    except:
                        pipe_send.send((False, traceback.format_exc()))
                except:
                    pipe_send.send((False, 'unknown error'))
            process = multiprocessing.Process(
                target=f__, args=args, kwargs=kwargs)
            import os
            import signal
            import time
            process.start()
            starttime = time.time()
            ok = pipe_recv.poll(seconds)
            endtime = time.time()
            if not ok:
                os.kill(process.pid, signal.SIGINT)
                ok = pipe_recv.poll(1)
                if not ok:
                    process.terminate()
                    duration = endtime - starttime
                    raise Exception('timed out after %r seconds' %
                        (duration,))
            ok, result = pipe_recv.recv()
            if not ok:
                raise Exception(result)
            return result
        return f_
    return wrap

def relerr(expected, actual):
  if expected == 0:
    return 0 if actual == 0 else 1
  else:
    return abs((actual - expected)/expected)

def collect_sp_samples(sp, args, seed, aux=None, nsamples=None):
    if nsamples is None:
        nsamples = default_num_samples()
    np_rng = npr.RandomState(seed)
    py_rng = random.Random(np_rng.randint(1, 2**31 - 1))
    sp_args = MockArgs(args, aux, py_rng=py_rng, np_rng=np_rng)
    sp0 = sp()
    return [sp0.simulate(sp_args) for _ in xrange(nsamples)]

BETA_SPACES = (
    ('beta', BetaOutputPSP, lambda x: x, 0, 1),
    ('log_beta', LogBetaOutputPSP, exp, float('-inf'), 0),
    ('log_odds_beta', LogOddsBetaOutputPSP, logistic,
     float('-inf'), float('+inf')),
)

def check_beta_density_quad(sp, lo, hi, a, b):
    sp0 = sp()
    args = MockArgs((a, b), None)
    def pdf(x):
        return exp(sp0.logDensity(x, args))
    one, esterr = scipy.integrate.quad(pdf, lo, hi)
    assert relerr(1, one) < esterr

def test_beta_density_quad():
    v = (.1, .25, .5, .75, 1, 2, 5, 10, 100)
    for _name, sp, _to_direct, lo, hi in BETA_SPACES:
        for a in v:
            for b in v:
                yield check_beta_density_quad, sp, lo, hi, a, b

@stochasticTest
def test_log_odds_uniform_cdf(seed):
    inf = float('inf')
    samples = collect_sp_samples(LogOddsUniformOutputPSP, (), seed)
    sp0 = LogOddsUniformOutputPSP()
    args = MockArgs((), None)
    def pdf(x):
        return exp(sp0.logDensity(x, args))
    def cdf(x):
        return logistic(x)
    for x in samples:
        p, e = scipy.integrate.quad(pdf, -inf, x)
        assert relerr(cdf(x), p) <= e

@statisticalTest
def check_beta_ks(name, sp, to_direct, lo, a, b, seed):
    samples = collect_sp_samples(sp, (a, b), seed)
    dist = scipy.stats.beta(a, b)
    return reportKnownContinuous(dist.cdf, map(to_direct, samples),
        descr='(%s %r %r)' % (name, a, b))

def test_beta_ks():
    v = (.1, .25, .5, 1, 1.1, 2, 5.5, 10)
    for name, sp, to_direct, lo, _hi in BETA_SPACES:
        for a in v:
            for b in v:
                if b < .5:
                    if 5 < a:
                        # The vast majority of the mass is squished up
                        # against 1, but we can't represent that
                        # adequately in direct-space.
                        continue
                yield check_beta_ks, name, sp, to_direct, lo, a, b

@statisticalTest
def check_beta_ks_quad(name, sp, lo, a, b, seed):
    samples = collect_sp_samples(sp, (a, b), seed)
    sp0 = sp()
    args = MockArgs((a, b), None)
    def pdf(x):
        return exp(sp0.logDensity(x, args))
    def cdf(x):
        p, e = scipy.integrate.quad(pdf, lo, x)
        assert p < 1 or relerr(1, p) < 100*e
        return min(p, 1)
    return reportKnownContinuous(np.vectorize(cdf), samples,
        descr='(%s %r %r)' % (name, a, b))

def test_beta_ks_quad():
    v = (.1, .25, .5, 1, 1.1, 5.5, 10)
    for name, sp, _to_direct, lo, _hi in BETA_SPACES:
        for a in v:
            for b in v:
                if name in ('beta', 'log_beta'):
                    if b < .5:
                        if 1 <= a:
                            # The vast majority of mass is squished up
                            # against 1, but we can't represent that
                            # adequately in direct-space and scipy's
                            # quadrature isn't able to accurately
                            # integrate such a sharp spike at 1.
                            continue
                yield check_beta_ks_quad, name, sp, lo, a, b

@statisticalTest
def test_beta_tail(seed):
    # Check that Beta(.1, .1) yields samples near 0 and 1, not just in
    # the middle.
    a = .1
    b = .1
    samples = collect_sp_samples(BetaOutputPSP, (a, b), seed)
    dist = scipy.stats.beta(a, b)
    return reportKnownContinuous(dist.cdf, samples, descr='(beta .1 .1)')

@on_inf_prim("none")
@stochasticTest
def test_beta_thagomizer(seed):
    # Check that Beta with spiky tails yields sane samples, not NaN.
    v = (1, 1/2, 1e-5, 1e-15, 1e-20, 1e-299, 1e-301)
    nsamples = 50
    np_rng = npr.RandomState(seed)
    for a in v:
        for b in v:
            seed = np_rng.randint(1, 2**31 - 1)
            samples = collect_sp_samples(BetaOutputPSP, (a, b), seed,
                nsamples=nsamples)
            for sample in samples:
                assert 0 <= sample
                assert sample <= 1
                if a < 1e-16 or b < 1e-16:
                    assert sample < 1e-16 or sample == 1

@timed(5)
@statisticalTest
def test_beta_small_small(seed):
    a = 5.5
    b = 5.5
    samples = collect_sp_samples(BetaOutputPSP, (a, b), seed)
    dist = scipy.stats.beta(a, b)
    return reportKnownContinuous(dist.cdf, samples, descr='(beta 5.5 5.5)')

@timed(5)
@statisticalTest
def test_beta_small_large(seed):
    a = 5.5
    b = 1e9
    samples = collect_sp_samples(BetaOutputPSP, (a, b), seed)
    dist = scipy.stats.beta(a, b)
    return reportKnownContinuous(dist.cdf, samples, descr='(beta 5.5 1e9)')

@timed(5)
@statisticalTest
def test_beta_large_small(seed):
    a = 1e9
    b = 5.5
    samples = collect_sp_samples(BetaOutputPSP, (a, b), seed)
    dist = scipy.stats.beta(a, b)
    return reportKnownContinuous(dist.cdf, samples, descr='(beta 1e9 5.5)')

@timed(5)
@stochasticTest
def test_beta_large_large(seed):
    a = 1e300
    b = 1e300
    samples = collect_sp_samples(BetaOutputPSP, (a, b), seed)
    assert all(sample == 1/2 for sample in samples)

@timed(5)
@stochasticTest
def test_log_beta_small(seed):
    a = 0.5
    b = 0.5
    samples = collect_sp_samples(LogBetaOutputPSP, (a, b), seed)

    # A single sample overflows with probability < F(10^{-10^300}),
    # where F is the CDF of Beta(1/2, 1/2), which is hard to evaluate
    # at such a tiny input but is probably smaller than we care about.
    assert all(not math.isinf(sample) for sample in samples)
    # A single sample is rounded to zero with probability < 10^-150.
    assert all(sample != 0 for sample in samples)

@timed(5)
@stochasticTest
def test_log_beta_bernoulli_small(seed):
    a = 0.5
    b = 0.5
    nsamples = default_num_samples()
    ripl = get_ripl(seed=seed)
    ripl.assume('p', '(log_beta %r %r)' % (a, b), label='p')
    ripl.observe('(log_bernoulli p)', 1, label='x')
    samples = collectSamples(ripl, 'p', nsamples)
    # A single sample overflows with probability < F(10^{-10^300}),
    # where F is the CDF of Beta(1/2, 1/2), which is hard to evaluate
    # at such a tiny input but is probably smaller than we care about.
    assert all(not math.isinf(sample) for sample in samples)
    # A single sample is rounded to zero with probability < 10^-150.
    assert all(sample != 0 for sample in samples)

@timed(5)
@stochasticTest
def test_log_beta_smaller(seed):
    a = 0.001
    b = 0.001
    samples = collect_sp_samples(LogBetaOutputPSP, (a, b), seed)
    # A single sample overflows with probability < F(10^{-10^300}),
    # where F is the CDF of Beta(0.001, 0.001), which is hard to
    # evaluate at such a tiny input but is probably smaller than we
    # care about.
    assert all(not math.isinf(sample) for sample in samples)
    # Unfortunately, the resolution around direct-space 1 / log-space
    # 0 is coarse enough that we plausibly get zero here.
    #assert all(sample != 0 for sample in samples)

@timed(5)
@stochasticTest
def test_log_beta_bernoulli_smaller(seed):
    a = 0.001
    b = 0.001
    nsamples = default_num_samples()
    ripl = get_ripl(seed=seed)
    ripl.assume('p', '(log_beta %r %r)' % (a, b), label='p')
    ripl.observe('(log_bernoulli p)', 1, label='x')
    samples = collectSamples(ripl, 'p', nsamples)
    # A single sample overflows with probability < F(10^{-10^300}),
    # where F is the CDF of Beta(0.001, 0.001), which is hard to
    # evaluate at such a tiny input but is probably smaller than we
    # care about.
    assert all(not math.isinf(sample) for sample in samples)
    # Unfortunately, the resolution around direct-space 1 / log-space
    # 0 is coarse enough that we plausibly get zero here.
    #assert all(sample != 0 for sample in samples)

@timed(5)
@stochasticTest
def test_log_odds_beta_small(seed):
    a = 0.5
    b = 0.5
    samples = collect_sp_samples(LogOddsBetaOutputPSP, (a, b), seed)
    # A single sample overflows with probability < F(10^{-10^300}),
    # where F is the CDF of Beta(1/2, 1/2), which is hard to evaluate
    # at such a tiny input but is probably smaller than we care about.
    assert all(not math.isinf(sample) for sample in samples)
    assert all(sample != 0 for sample in samples)

@timed(5)
@stochasticTest
def test_log_odds_beta_bernoulli_small(seed):
    a = 0.5
    b = 0.5
    nsamples = default_num_samples()
    ripl = get_ripl(seed=seed)
    ripl.assume('p', '(log_odds_beta %r %r)' % (a, b), label='p')
    ripl.observe('(log_odds_bernoulli p)', 1, label='x')
    samples = collectSamples(ripl, 'p', nsamples)
    # A single sample overflows with probability < F(10^{-10^300}),
    # where F is the CDF of Beta(1/2, 1/2), which is hard to evaluate
    # at such a tiny input but is probably smaller than we care about.
    assert all(not math.isinf(sample) for sample in samples)
    assert all(sample != 0 for sample in samples)

@timed(5)
@stochasticTest
def test_log_odds_beta_smaller(seed):
    a = 0.001
    b = 0.001
    samples = collect_sp_samples(LogOddsBetaOutputPSP, (a, b), seed)
    # A single sample overflows with probability < F(10^{-10^300}),
    # where F is the CDF of Beta(0.001, 0.001), which is hard to
    # evaluate at such a tiny input but is probably smaller than we
    # care about.
    assert all(not math.isinf(sample) for sample in samples)
    assert all(sample != 0 for sample in samples)

@timed(5)
@stochasticTest
def test_log_odds_beta_bernoulli_smaller(seed):
    a = 0.001
    b = 0.001
    nsamples = default_num_samples()
    ripl = get_ripl(seed=seed)
    ripl.assume('p', '(log_odds_beta %r %r)' % (a, b), label='p')
    ripl.observe('(log_odds_bernoulli p)', 1, label='x')
    samples = collectSamples(ripl, 'p', nsamples)
    # A single sample overflows with probability < F(10^{-10^300}),
    # where F is the CDF of Beta(0.001, 0.001), which is hard to
    # evaluate at such a tiny input but is probably smaller than we
    # care about.
    assert all(not math.isinf(sample) for sample in samples)
    assert all(sample != 0 for sample in samples)
