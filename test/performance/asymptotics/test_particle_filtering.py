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
from nose.plugins.attrib import attr

from venture.test.config import broken_in
from venture.test.config import get_ripl
from venture.test.config import on_inf_prim
import venture.test.timing as timing

@attr('slow')
@on_inf_prim("resample")
def testHMMParticleAsymptotics1():
  num_particles = 5
  def particulate(num_steps):
    ripl = get_ripl()
    ripl.infer("(resample %s)" % num_particles)

    def do_filter():
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

    return do_filter

  timing.assertLinearTime(particulate, verbose=True, acceptable_duration=300, desired_sample_ct=40)

# TODO This is the version that uses mem like one normally would.
# Right now it's broken because freeze is only known to work on
# directives.

@attr('slow')
@on_inf_prim("resample")
@broken_in("puma", "Puma still freezes shallowly.  Issue #626")
@broken_in("lite", "Lite still freezes shallowly.  Issue #626")
def testHMMParticleAsymptoticsMem():
  num_particles = 5
  def freeze_exp(ripl, exp):
    ripl.predict(exp, label="do not clash with me")
    ripl.freeze("do not clash with me")
    ripl.forget("do not clash with me")

  def particulate(num_steps):
    ripl = get_ripl()
    ripl.infer("(resample %s)" % num_particles)
    ripl.execute_program("""
[assume state (mem (lambda (t)
  (if (<= t 0)
      (normal 0.0 1.0)
      (normal (state (- t 1)) 1.0))))]
""")
    def do_filter():
      for m in range(num_steps):
        newValue = scipy.stats.norm.rvs(0,1.0)
        ripl.observe("(normal (state %d) 1.0)" % m, newValue, label="obs%d" % m)
        if m > 0:
          freeze_exp(ripl, "(state %s)" % (m-1))
          ripl.forget("obs%d" % (m-1))
        ripl.infer("(resample %s)" % num_particles)

    return do_filter

  timing.assertLinearTime(particulate, verbose=True, acceptable_duration=300, desired_sample_ct=40)
