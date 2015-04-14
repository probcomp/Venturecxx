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

from nose.tools import eq_
from venture.test.config import get_ripl, on_inf_prim, broken_in

@broken_in('puma', 'zip SP not implemented in Puma')
@on_inf_prim("none")
def testZip1():
  eq_(get_ripl().predict("(zip)"), [])

@broken_in('puma', 'zip SP not implemented in Puma')
@on_inf_prim("none")
def testZip2():
  eq_(get_ripl().predict("(zip (list 1))"), [[1.0]])

@broken_in('puma', 'zip SP not implemented in Puma')
@on_inf_prim("none")
def testZip3():
  '''Should work with any # of input lists. Arrays, lists, and vectors should work'''
  pred = "(zip (array 1 2 3) (list 4 5 6) (vector 7 8 9))"
  res = [[1.0,4.0,7.0], [2.0,5.0,8.0], [3.0,6.0,9.0]]
  eq_(get_ripl().predict(pred), res)

@broken_in('puma', 'zip SP not implemented in Puma')
@on_inf_prim("none")
def testZip4():
  '''If one list is shorter, truncate the output'''
  pred = "(zip (array 1 2 3) (list 4 5 6) (vector 7 8))"
  res = [[1.0,4.0,7.0], [2.0,5.0,8.0]]
  eq_(get_ripl().predict(pred), res)
