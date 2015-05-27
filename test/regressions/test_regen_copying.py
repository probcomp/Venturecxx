# Copyright (c) 2015 MIT Probabilistic Computing Project.
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

from venture.test.config import get_ripl, broken_in

def testCopyingChoiceAfterObservation():
  """Conjecture: makeConsistent may actually be stochastic, if there are
random choices downstream from nodes that get constrained.

Conjecture: in this case, Lite-style copying may change both the
source and target trace, perhaps differently.

We use registerConstraints instead of makeConsistent during copying
in order to avoid this problem.
"""
  ripl = get_ripl()
  ripl.execute_program('''
[assume c (flip)]
[observe c true]
[infer (incorporate)]
[assume x (if c (flip) (flip))]
''')
  old_x = ripl.sample("x")
  for _ in range(10):
    trace = ripl.sivm.core_sivm.engine.getDistinguishedTrace() # Should not copy without multiprocessing
    _ = ripl.sivm.core_sivm.engine.model.copy_trace(trace)
    new_x = ripl.sample("x")
    eq_(old_x, new_x)
