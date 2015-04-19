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

from venture.test.config import get_ripl, on_inf_prim
import venture.test.timing as timing

def loadHMMParticleAsymptoticProgram1(M):
  """Easiest possible HMM asymptotic test for particles"""
  ripl = get_ripl()

  ripl.assume("f","""
(mem (lambda (i)
  (if (eq i 0)
    (tag (quote states) 0 (normal 0.0 1.0))
    (tag (quote states) i (normal (f (- i 1)) 1.0)))))
""")
  ripl.assume("g","""
(mem (lambda (i)
  (normal (f i) 1.0)))
""")

  previousValue = 0.0
  for m in range(M):
    newValue = scipy.stats.norm.rvs(previousValue,1.0)
    ripl.observe("(g %d)" % m,"%d" % newValue)
    previousValue = newValue

  return ripl


# O(N) forwards
# O(N log N) to infer
@attr('slow')
@on_inf_prim("func_pgibbs")
def testHMMParticleAsymptotics1():
  def particulate(num_steps):
    ripl = loadHMMParticleAsymptoticProgram1(num_steps)
    return lambda : ripl.infer("(func_pgibbs states ordered 10 5)")

  timing.assertNLogNTime(particulate)
