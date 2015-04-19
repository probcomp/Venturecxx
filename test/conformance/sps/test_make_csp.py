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
from nose.tools import assert_equals

@on_inf_prim("none")
def testMakeCSP1():
  ripl = get_ripl()
  ripl.assume("f", "(lambda (x) (* x x))")
  ripl.predict("(f 1)",label="pid")
  assert_equals(ripl.report("pid"),1.0)

@on_inf_prim("none")
def testMakeCSP2():
  ripl = get_ripl()
  ripl.assume("g", "(lambda (x y) (* x y))")
  ripl.predict("(g 2 3)",label="pid")
  assert_equals(ripl.report("pid"),6.0)

@on_inf_prim("none")
def testMakeCSP3():
  ripl = get_ripl()
  ripl.assume("h", "(lambda () 5)")
  ripl.predict("(h)",label="pid")
  assert_equals(ripl.report("pid"),5.0)

@on_inf_prim("none")
def testMakeCSP4():
  ripl = get_ripl()
  ripl.assume("f", "(lambda (x y z) (lambda (u v w) (lambda () (+ (* x u) (* y v) (* z w)))))")
  ripl.assume("g", "(f 10 20 30)")
  ripl.assume("h","(g 3 5 7)")
  ripl.predict("(h)",label="pid")
  assert_equals(ripl.report("pid"),340)
