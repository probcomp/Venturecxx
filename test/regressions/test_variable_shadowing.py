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

from venture.test.config import get_ripl

def testVariableShadowing():
  """Prior to the patch in which we implemented Trace.sealEnvironment(), we were
  able to destructively redefine symbols from the inference prelude, and things
  exploded.  Now we should see a shadowing behavior when we try similar
  definitions.
"""
  ripl = get_ripl()
  ripl.execute_program('''
[assume x (normal 0 1)]
[define repeat 3]
[infer (accumulate_dataset 10 (do (collect x)))]
''')
  eq_(ripl.evaluate('repeat'), ripl.evaluate('3.0'))
