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

from nose.tools import assert_equals, eq_

from venture.test.config import get_ripl, broken_in, on_inf_prim
from venture.test.errors import assert_error_message_contains

@on_inf_prim("none")
def testFix1():
  ripl = get_ripl()
  ripl.predict("""
(letrec ((f (lambda (n) (if (> n 0) (f (- n 1)) 17))))
  (f 5))
""", label="pid")
  assert_equals(ripl.report("pid"), 17.0)

@on_inf_prim("none")
def testFix1b():
  ripl = get_ripl()
  eq_(17.0, ripl.evaluate("""
(letrec ((f (lambda (n) (if (> n 0) (f (- n 1)) 17))))
  (f 5))
"""))

@on_inf_prim("none")
def testFix2():
  ripl = get_ripl()
  ripl.predict("""
(letrec ((even (lambda (n) (if (> n 0) (odd (- n 1)) true)))
         (odd (lambda (n) (if (> n 0) (even (- n 1)) false))))
  (odd 5))
""", label="pid")
  assert_equals(ripl.report("pid"), True)

@on_inf_prim("none")
def testFixMem():
  ripl = get_ripl()
  ripl.predict("""
(letrec ((fib (mem (lambda (n)
    (if (> n 1)
        (+ (fib (- n 1))
           (fib (- n 2)))
        1)))))
  (fib 15))
""", label="pid")
  assert_equals(ripl.report("pid"), 987.0)

@broken_in("puma", "Puma raises RuntimeError instead of VentureException")
@on_inf_prim("none")
def testFixScope():
  ripl = get_ripl()
  assert_error_message_contains("Cannot find symbol 'x'", ripl.predict, """\
(let ((x 5))
  (letrec ((x x))
    x))
""", label="pid")
