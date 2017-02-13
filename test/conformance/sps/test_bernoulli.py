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

from nose.tools import assert_raises

from venture.exception import VentureException
from venture.test.config import get_ripl

def test_bernoulli_range_error():
    ripl = get_ripl(init_mode='venture_script')
    ripl.sample('bernoulli(0.0)')
    ripl.sample('bernoulli(0.5)')
    ripl.sample('bernoulli(1.0)')
    with assert_raises(VentureException):
        ripl.sample('bernoulli(-0.1)')
    with assert_raises(VentureException):
        ripl.sample('bernoulli(1.1)')

def test_flip_range_error():
    ripl = get_ripl(init_mode='venture_script')
    ripl.sample('flip(0.0)')
    ripl.sample('flip(0.5)')
    ripl.sample('flip(1.0)')
    with assert_raises(VentureException):
        ripl.sample('flip(-0.1)')
    with assert_raises(VentureException):
        ripl.sample('flip(1.1)')

def test_log_bernoulli_range_error():
    ripl = get_ripl(init_mode='venture_script')
    ripl.sample('log_bernoulli(-1.0)')
    ripl.sample('log_bernoulli(0.0)')
    with assert_raises(VentureException):
        ripl.sample('log_bernoulli(1.0)')

def test_log_flip_range_error():
    ripl = get_ripl(init_mode='venture_script')
    ripl.sample('log_flip(-1.0)')
    ripl.sample('log_flip(0.0)')
    with assert_raises(VentureException):
        ripl.sample('log_flip(1.0)')
