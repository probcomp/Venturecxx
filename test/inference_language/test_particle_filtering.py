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

import scipy.stats

from venture.test.config import get_ripl, on_inf_prim

# TODO Rewrite this to use mem like one normally would.  Right now
# it's metaprogrammed because freeze is only known to work on
# directives.

@on_inf_prim("resample")
def testHMMParticleSmoke():
  num_particles = 3
  num_steps = 10

  ripl = get_ripl()
  ripl.infer("(resample %s)" % num_particles)

  for m in range(num_steps):
    newValue = scipy.stats.norm.rvs(0,1.0)
    if m == 0:
      ripl.assume("state_0", "(normal 0.0 1.0)", label="st0")
    else:
      ripl.assume("state_%d" % m, "(normal state_%d 1.0)" % (m-1), label="st%s" % m)
    ripl.observe("(normal state_%d 1.0)" % m, newValue, label="obs%d" % m)
    if m > 0:
      ripl.freeze("st%s" % (m-1))
      ripl.forget("obs%d" % (m-1))
    if m > 1:
      ripl.forget("st%s" % (m-2))
    ripl.infer("(resample %s)" % num_particles)

  # TODO What, actually, are the distributions we expect?  Can a
  # version of this (with more particles?) be a statistical test?
