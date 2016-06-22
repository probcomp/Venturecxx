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

import multiprocessing
import nose.tools
import scipy.stats
import traceback

from venture.test.config import broken_in
from venture.test.config import collectSamples
from venture.test.config import default_num_samples
from venture.test.config import get_ripl
from venture.test.config import on_inf_prim
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
def test_beta_tail():
    # Check that Beta(.1, .1) yields samples near 0 and 1, not just in
    # the middle.
    a = .1
    b = .1
    nsamples = default_num_samples()
    expression = '(beta %r %r)' % (a, b)
    ripl = get_ripl()
    ripl.assume('p', expression, label='p')
    samples = collectSamples(ripl, 'p', nsamples)
    dist = scipy.stats.beta(a, b)
    return reportKnownContinuous(dist.cdf, samples, descr=expression)

@broken_in("puma", "Issue #504")
@on_inf_prim("none")
def test_beta_thagomizer():
    # Check that Beta with spiky tails yields sane samples, not NaN.
    v = (1, 1/2, 1e-5, 1e-15, 1e-20, 1e-299, 1e-301)
    nsamples = 50
    for a in v:
        for b in v:
            expression = '(beta %r %r)' % (a, b)
            ripl = get_ripl()
            for _ in xrange(nsamples):
                sample = ripl.sample(expression)
                assert 0 <= sample
                assert sample <= 1
                if a < 1e-16 or b < 1e-16:
                    assert sample < 1e-16 or sample == 1

@timed(5)
@statisticalTest
def test_beta_small_small():
    a = 5.5
    b = 5.5
    nsamples = default_num_samples()
    expression = '(beta %r %r)' % (a, b)
    ripl = get_ripl()
    ripl.assume('p', expression, label='p')
    samples = collectSamples(ripl, 'p', nsamples)
    dist = scipy.stats.beta(a, b)
    return reportKnownContinuous(dist.cdf, samples, descr=expression)

@timed(5)
@statisticalTest
def test_beta_small_large():
    a = 5.5
    b = 1e9
    nsamples = default_num_samples()
    expression = '(beta %r %r)' % (a, b)
    ripl = get_ripl()
    ripl.assume('p', expression, label='p')
    samples = collectSamples(ripl, 'p', nsamples)
    dist = scipy.stats.beta(a, b)
    return reportKnownContinuous(dist.cdf, samples, descr=expression)

@timed(5)
@statisticalTest
def test_beta_large_small():
    a = 1e9
    b = 5.5
    nsamples = default_num_samples()
    expression = '(beta %r %r)' % (a, b)
    ripl = get_ripl()
    ripl.assume('p', expression, label='p')
    samples = collectSamples(ripl, 'p', nsamples)
    dist = scipy.stats.beta(a, b)
    return reportKnownContinuous(dist.cdf, samples, descr=expression)

@timed(5)
def test_beta_large_large():
    a = 1e300
    b = 1e300
    nsamples = default_num_samples()
    expression = '(beta %r %r)' % (a, b)
    ripl = get_ripl()
    ripl.assume('p', expression, label='p')
    samples = collectSamples(ripl, 'p', nsamples)
    assert all(sample == 1/2 for sample in samples)
