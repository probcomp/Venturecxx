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

import sys
from nose.plugins.attrib import attr

from venture.test.config import get_ripl, on_inf_prim
import venture.test.timing as timing

sys.setrecursionlimit(1000000) 

def loadChurchPairProgram(K):
  ripl = get_ripl()

  ripl.assume("make_church_pair","(lambda (x y) (lambda (f) (if (= f 0) x y)))")
  ripl.assume("church_pair_lookup","(lambda (cp n) (if (= n 0) (cp 0) (church_pair_lookup (cp 1) (- n 1))))")
  ripl.assume("cp0","(make_church_pair (flip 0.5) 0)")
    
  for i in range(K):
    ripl.assume('cp%d' % (i+1), '(make_church_pair (flip) cp%d)' % i)

  ripl.predict('(church_pair_lookup cp%d %d)' % (K, K))
  return ripl


# O(N) forwards
# O(1) to infer
@attr('slow')
@on_inf_prim("mh")
def testChurchPairProgram1():

  def pairify(K):
    ripl = loadChurchPairProgram(K)
    return lambda : ripl.infer(100)

  timing.assertConstantTime(pairify)


def loadReferencesProgram(K):
  ripl = get_ripl()
  ripl.assume("make_ref","(lambda (x) (lambda () x))")
  ripl.assume("deref","(lambda (r) (r))")

  ripl.assume("cp0","(list (make_ref (flip)))")
    
  for i in range(K):
    ripl.assume('cp%d' % (i+1), '(pair (make_ref (flip)) cp%d)' % i)

  ripl.predict('(deref (lookup cp%d %d))' % (K, K))
  return ripl

# O(N) forwards
# O(1) to infer
# (this could be reused from testChurchPairProgram)
@attr('slow')
@on_inf_prim("mh")
def testReferencesProgram1():

  def refify(K):
    ripl = loadReferencesProgram(K)
    return lambda : ripl.infer(100)

  timing.assertConstantTime(refify)
