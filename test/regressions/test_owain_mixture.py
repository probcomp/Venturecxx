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

from venture.test.config import get_ripl, on_inf_prim

@on_inf_prim("mh")
def testOwainMixture():
  """Owain got <Exception: Cannot make random choices downstream of a node that gets constrained during regen> and thinks this is a mistake. DHS cannot reproduce the error."""
  ripl = get_ripl()
  ripl.assume("alpha","(uniform_continuous .01 1)")
  ripl.assume("crp","(make_crp alpha)")
  ripl.assume("z","(mem (lambda (i) (crp) ) )")
  ripl.assume("mu","(mem (lambda (z) (normal 0 5) ) )")
  ripl.assume("sig","(mem (lambda (z) (uniform_continuous .1 8) ) )")

  ripl.assume("x","(mem (lambda (i) (normal (mu (z i)) (sig (z i))))  )")

  ripl.assume("w","(lambda (z) 1)")
  ripl.assume("f","(lambda (z x) (* (w z) x) )")

  ripl.assume("y","(mem (lambda (i) (normal (f (z i) (x i)) .1) ) )")

  for i in range(10):
    ripl.observe('(x %i)' %i, '%f' % 1.0)
    ripl.observe('(y %i)' %i, '%f' % 2.0)

  for i in range(10,20):
    ripl.observe('(x %i)'%i,'%f' % 3)
    ripl.infer(10)
    for _ in range(20):
      ripl.predict(["y", i])

  ripl.infer(100)
  
  
  ## without memoizing y's

  ripl = get_ripl()
  ripl.assume("alpha","(uniform_continuous .01 1)")
  ripl.assume("crp","(make_crp alpha)")
  ripl.assume("z","(mem (lambda (i) (crp) ) )")
  ripl.assume("mu","(mem (lambda (z) (normal 0 5) ) )")
  ripl.assume("sig","(mem (lambda (z) (uniform_continuous .1 8) ) )")

  ripl.assume("x","(mem (lambda (i) (normal (mu (z i)) (sig (z i))))  )")

  ripl.assume("w","(lambda (z) 1)")
  ripl.assume("f","(lambda (z x) (* (w z) x) )")

  ripl.assume("y","(lambda (i) (normal (f (z i) (x i)) .1) )")

  for i in range(10):
    ripl.observe('(x %i)' %i, '%f' % 1.0)
    ripl.observe('(y %i)' %i, '%f' % 2.0)

  for i in range(10,20):
    ripl.observe('(x %i)'%i,'%f' % 3)
    ripl.infer(10)
    for _ in range(20):
      ripl.predict(["y", i])

  ripl.infer(100)
