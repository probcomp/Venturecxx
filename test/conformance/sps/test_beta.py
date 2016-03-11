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

import scipy.stats
from venture.test.config import collectSamples
from venture.test.config import default_num_samples
from venture.test.config import get_ripl
from venture.test.stats import reportKnownContinuous
from venture.test.stats import statisticalTest

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
