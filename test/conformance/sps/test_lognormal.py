# Copyright (c) 2017 MIT Probabilistic Computing Project.
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

from venture.test.config import get_ripl

def test_lognormal_rejection_x():
  r = get_ripl(init_mode='venture_script')
  r.assume('x', 'lognormal(2, 1)')
  r.observe('log_bernoulli(-x)', '1')
  r.infer('rejection(default, all, 0, 1)')

def test_lognormal_rejection_mu():
  r = get_ripl(init_mode='venture_script')
  r.assume('mu', 'expon(2)')
  r.observe('lognormal(mu, 1)', '0.5')
  r.infer('rejection(default, all, 0, 1)')

def test_lognormal_rejection_sigma():
  r = get_ripl(init_mode='venture_script')
  r.assume('sigma', 'expon(1)')
  r.observe('lognormal(2, sigma)', '0.5')
  r.infer('rejection(default, all, 0, 1)')
