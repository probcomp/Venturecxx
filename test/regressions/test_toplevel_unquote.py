# Copyright (c) 2015, 2016 MIT Probabilistic Computing Project.
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
from venture.test.config import on_inf_prim

@on_inf_prim("unquote")
def testUnquoteWorksAtToplevel():
  r = get_ripl()
  r.set_mode('venture_script')
  ans = r.execute_program('''
define y = 42;
sample unquote(y) + 1;
sample(unquote(y) + 2);
  ''', type=False)
  eq_(ans, [42.0, 43.0, 44.0])

@on_inf_prim("unquote")
def testUnquotePermitsModelMacroExpansion():
  r = get_ripl()
  ans = r.evaluate('(predict (let ((x (unquote (+ 2 2)))) (+ x x)))')
  eq_(ans, 8.0)
