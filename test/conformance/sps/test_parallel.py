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

from nose.tools import assert_raises

from venture.exception import VentureException

from venture.test.config import get_ripl
from venture.test.config import on_inf_prim

@on_inf_prim('none')
def test_parallel_mapv():
  boxed_result = get_ripl().evaluate(
    '(parallel_mapv (lambda (x) (+ x 1)) (array 1 2 3) 2)')
  result = [r.getNumber() for r in boxed_result]
  assert result == [2, 3, 4], '%r' % (result,)

@on_inf_prim('none')
def test_parallel_mapv_traced():
  assert_raises(VentureException, lambda:
    get_ripl().sample('(parallel_mapv (lambda (x) (+ x 1)) (array 1 2 3) 2)'))

@on_inf_prim('none')
def test_parallel_mapv_error():
  assert_raises(VentureException, lambda:
    get_ripl().evaluate('(parallel_mapv (lambda (x) y) (array 1 2 3) 2)'))
