# Copyright (c) 2016 MIT Probabilistic Computing Project.
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

from nose.tools import eq_

from venture.test.config import get_ripl

from venture.mite import address
import venture.ripl.utils as u

def test_random_site_sim_smoke():
  prog = """
[define random_site (random_site_)]
(eval_in (do (assume x (normal 0 1)) (random_site)) (flat_trace))
"""
  ans = get_ripl().execute_program(prog)
  assert isinstance(u.strip_types(ans[1]["value"]), address.DirectiveAddress)

def test_random_site_assess_smoke():
  prog = """
[define random_site (random_site_)]
(eval_in
 (do (assume x (normal 0 1))
     (invoke_metaprogram_of_action_sp random_site 'log_density_action (array (by_walk (by_top) 1))))
 (flat_trace))"""
  ans = get_ripl().execute_program(prog)
  eq_(u.strip_types(ans[1]["value"]), 0.0)
