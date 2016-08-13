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
import traceback

import nose.tools
import scipy.stats

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
            process.start()
            ok = pipe_recv.poll(seconds)
            process.terminate()
            if not ok:
                raise Exception('timed out')
            ok, result = pipe_recv.recv()
            if not ok:
                raise Exception(result)
            return result
        return f_
    return wrap

@statisticalTest
def test_beta_tail(seed):
    # Check that Beta(.1, .1) yields samples near 0 and 1, not just in
    # the middle.
    a = .1
    b = .1
    nsamples = default_num_samples()
    expression = '(beta %r %r)' % (a, b)
    ripl = get_ripl(seed=seed)
    ripl.assume('p', expression, label='p')
    samples = collectSamples(ripl, 'p', nsamples)
    dist = scipy.stats.beta(a, b)
    return reportKnownContinuous(dist.cdf, samples, descr=expression)

@broken_in("puma", "Issue #504")
@on_inf_prim("none")
@stochasticTest
def test_beta_thagomizer(seed):
    # Check that Beta with spiky tails yields sane samples, not NaN.
    v = (1, 1/2, 1e-5, 1e-15, 1e-20, 1e-299, 1e-301)
    nsamples = 50
    for a in v:
        for b in v:
            expression = '(beta %r %r)' % (a, b)
            ripl = get_ripl(seed=seed)
            for _ in xrange(nsamples):
                sample = ripl.sample(expression)
                assert 0 <= sample
                assert sample <= 1
                if a < 1e-16 or b < 1e-16:
                    assert sample < 1e-16 or sample == 1

@timed(5)
@statisticalTest
def test_beta_small_small(seed):
    a = 5.5
    b = 5.5
    nsamples = default_num_samples()
    expression = '(beta %r %r)' % (a, b)
    ripl = get_ripl(seed=seed)
    ripl.assume('p', expression, label='p')
    samples = collectSamples(ripl, 'p', nsamples)
    dist = scipy.stats.beta(a, b)
    return reportKnownContinuous(dist.cdf, samples, descr=expression)

@timed(5)
@statisticalTest
def test_beta_small_large(seed):
    a = 5.5
    b = 1e9
    nsamples = default_num_samples()
    expression = '(beta %r %r)' % (a, b)
    ripl = get_ripl(seed=seed)
    ripl.assume('p', expression, label='p')
    samples = collectSamples(ripl, 'p', nsamples)
    dist = scipy.stats.beta(a, b)
    return reportKnownContinuous(dist.cdf, samples, descr=expression)

@timed(5)
@statisticalTest
def test_beta_large_small(seed):
    a = 1e9
    b = 5.5
    nsamples = default_num_samples()
    expression = '(beta %r %r)' % (a, b)
    ripl = get_ripl(seed=seed)
    ripl.assume('p', expression, label='p')
    samples = collectSamples(ripl, 'p', nsamples)
    dist = scipy.stats.beta(a, b)
    return reportKnownContinuous(dist.cdf, samples, descr=expression)

@timed(5)
@stochasticTest
def test_beta_large_large(seed):
    a = 1e300
    b = 1e300
    nsamples = default_num_samples()
    expression = '(beta %r %r)' % (a, b)
    ripl = get_ripl(seed=seed)
    ripl.assume('p', expression, label='p')
    samples = collectSamples(ripl, 'p', nsamples)
    assert all(sample == 1/2 for sample in samples)

def test_log_beta_small():
    a = 0.5
    b = 0.5
    nsamples = default_num_samples()
    expression = '(log_beta %r %r)' % (a, b)
    ripl = get_ripl()
    ripl.assume('p', expression, label='p')
    samples = collectSamples(ripl, 'p', nsamples)
    # A single sample overflows with probability < F(10^{-10^300}),
    # where F is the CDF of Beta(1/2, 1/2), which is hard to evaluate
    # at such a tiny input but is probably smaller than we care about.
    assert all(not math.isinf(sample) for sample in samples)
    # A single sample is rounded to zero with probability < 10^-150.
    assert all(sample != 0 for sample in samples)

def test_log_beta_bernoulli_small():
    a = 0.5
    b = 0.5
    nsamples = default_num_samples()
    ripl = get_ripl()
    ripl.assume('p', '(log_beta %r %r)' % (a, b), label='p')
    ripl.observe('(log_bernoulli p)', 1, label='x')
    samples = collectSamples(ripl, 'p', nsamples)
    # A single sample overflows with probability < F(10^{-10^300}),
    # where F is the CDF of Beta(1/2, 1/2), which is hard to evaluate
    # at such a tiny input but is probably smaller than we care about.
    assert all(not math.isinf(sample) for sample in samples)
    # A single sample is rounded to zero with probability < 10^-150.
    assert all(sample != 0 for sample in samples)

def test_log_beta_smaller():
    a = 0.001
    b = 0.001
    nsamples = default_num_samples()
    expression = '(log_beta %r %r)' % (a, b)
    ripl = get_ripl()
    ripl.assume('p', expression, label='p')
    samples = collectSamples(ripl, 'p', nsamples)
    # A single sample overflows with probability < F(10^{-10^300}),
    # where F is the CDF of Beta(0.001, 0.001), which is hard to
    # evaluate at such a tiny input but is probably smaller than we
    # care about.
    assert all(not math.isinf(sample) for sample in samples)
    # Unfortunately, the resolution around direct-space 1 / log-space
    # 0 is coarse enough that we plausibly get zero here.
    #assert all(sample != 0 for sample in samples)

def test_log_beta_bernoulli_smaller():
    a = 0.001
    b = 0.001
    nsamples = default_num_samples()
    ripl = get_ripl()
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

def test_log_odds_beta_small():
    a = 0.5
    b = 0.5
    nsamples = default_num_samples()
    expression = '(log_odds_beta %r %r)' % (a, b)
    ripl = get_ripl()
    ripl.assume('p', expression, label='p')
    samples = collectSamples(ripl, 'p', nsamples)
    # A single sample overflows with probability < F(10^{-10^300}),
    # where F is the CDF of Beta(1/2, 1/2), which is hard to evaluate
    # at such a tiny input but is probably smaller than we care about.
    assert all(not math.isinf(sample) for sample in samples)
    assert all(sample != 0 for sample in samples)

def test_log_odds_beta_bernoulli_small():
    a = 0.5
    b = 0.5
    nsamples = default_num_samples()
    ripl = get_ripl()
    ripl.assume('p', '(log_odds_beta %r %r)' % (a, b), label='p')
    ripl.observe('(log_odds_bernoulli p)', 1, label='x')
    samples = collectSamples(ripl, 'p', nsamples)
    # A single sample overflows with probability < F(10^{-10^300}),
    # where F is the CDF of Beta(1/2, 1/2), which is hard to evaluate
    # at such a tiny input but is probably smaller than we care about.
    assert all(not math.isinf(sample) for sample in samples)
    assert all(sample != 0 for sample in samples)

def test_log_odds_beta_smaller():
    a = 0.001
    b = 0.001
    nsamples = default_num_samples()
    expression = '(log_odds_beta %r %r)' % (a, b)
    ripl = get_ripl()
    ripl.assume('p', expression, label='p')
    samples = collectSamples(ripl, 'p', nsamples)
    # A single sample overflows with probability < F(10^{-10^300}),
    # where F is the CDF of Beta(0.001, 0.001), which is hard to
    # evaluate at such a tiny input but is probably smaller than we
    # care about.
    assert all(not math.isinf(sample) for sample in samples)
    assert all(sample != 0 for sample in samples)

def test_log_odds_beta_bernoulli_smaller():
    a = 0.001
    b = 0.001
    nsamples = default_num_samples()
    ripl = get_ripl()
    ripl.assume('p', '(log_odds_beta %r %r)' % (a, b), label='p')
    ripl.observe('(log_odds_bernoulli p)', 1, label='x')
    samples = collectSamples(ripl, 'p', nsamples)
    # A single sample overflows with probability < F(10^{-10^300}),
    # where F is the CDF of Beta(0.001, 0.001), which is hard to
    # evaluate at such a tiny input but is probably smaller than we
    # care about.
    assert all(not math.isinf(sample) for sample in samples)
    assert all(sample != 0 for sample in samples)
