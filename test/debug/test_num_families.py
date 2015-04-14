# Copyright (c) 2013, 2014 MIT Probabilistic Computing Project.
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

from nose.tools import assert_equal

from venture.test.config import get_ripl, broken_in, on_inf_prim

@broken_in('lite', "numFamilies is only implemented in puma")
@on_inf_prim("none")
def testNumFamilies1():
  """A sanity test for numFamilies"""
  ripl = get_ripl()
  ripl.assume("rain","(bernoulli 0.2)")
  ripl.assume("sprinkler","(if rain (bernoulli 0.01) (bernoulli 0.4))")
  ripl.assume("grassWet","""
(if rain
  (if sprinkler (bernoulli 0.99) (bernoulli 0.8))
  (if sprinkler (bernoulli 0.9)  (bernoulli 0.00001)))
""")
  ripl.observe("grassWet", True)

  numFamilies = ripl.sivm.core_sivm.engine.getDistinguishedTrace().numFamilies()
  assert_equal(numFamilies,[4,1,1,1])
