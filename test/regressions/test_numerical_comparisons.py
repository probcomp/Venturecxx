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
from venture.test.config import gen_on_inf_prim

@gen_on_inf_prim("none")
def testNumericComparisons():
  for lhs in ["real", "integer", "probability"]:
    for rhs in ["real", "integer", "probability"]:
      yield checkLt, lhs, rhs
      yield checkEq, lhs, rhs
      yield checkGt, lhs, rhs

def checkLt(lhs, rhs):
  r = get_ripl()
  eq_(r.sample("(<  %s<0> %s<1>)" % (lhs, rhs)), True)
  eq_(r.sample("(<= %s<0> %s<1>)" % (lhs, rhs)), True)
  eq_(r.sample("(>  %s<0> %s<1>)" % (lhs, rhs)), False)
  eq_(r.sample("(>= %s<0> %s<1>)" % (lhs, rhs)), False)
  eq_(r.sample("( = %s<0> %s<1>)" % (lhs, rhs)), False)

def checkEq(lhs, rhs):
  r = get_ripl()
  eq_(r.sample("(<  %s<1> %s<1>)" % (lhs, rhs)), False)
  eq_(r.sample("(<= %s<1> %s<1>)" % (lhs, rhs)), True)
  eq_(r.sample("(>  %s<1> %s<1>)" % (lhs, rhs)), False)
  eq_(r.sample("(>= %s<1> %s<1>)" % (lhs, rhs)), True)
  eq_(r.sample("( = %s<1> %s<1>)" % (lhs, rhs)), True)

def checkGt(lhs, rhs):
  r = get_ripl()
  eq_(r.sample("(<  %s<1> %s<0>)" % (lhs, rhs)), False)
  eq_(r.sample("(<= %s<1> %s<0>)" % (lhs, rhs)), False)
  eq_(r.sample("(>  %s<1> %s<0>)" % (lhs, rhs)), True)
  eq_(r.sample("(>= %s<1> %s<0>)" % (lhs, rhs)), True)
  eq_(r.sample("( = %s<1> %s<0>)" % (lhs, rhs)), False)

@gen_on_inf_prim("none")
def testAtomicComparisons():
  # Note the answers in the below -- all atoms are bigger than all
  # numbers.
  for lhs in ["real", "integer", "probability"]:
    yield checkLtAtom, lhs
    yield checkEqAtom, lhs
    yield checkGtAtom, lhs

def checkLtAtom(lhs):
  r = get_ripl()
  eq_(r.sample("(<  %s<0> atom<1>)" % (lhs,)), True)
  eq_(r.sample("(<= %s<0> atom<1>)" % (lhs,)), True)
  eq_(r.sample("(>  %s<0> atom<1>)" % (lhs,)), False)
  eq_(r.sample("(>= %s<0> atom<1>)" % (lhs,)), False)
  eq_(r.sample("( = %s<0> atom<1>)" % (lhs,)), False)

def checkEqAtom(lhs):
  r = get_ripl()
  eq_(r.sample("(<  %s<1> atom<1>)" % (lhs,)), True)
  eq_(r.sample("(<= %s<1> atom<1>)" % (lhs,)), True)
  eq_(r.sample("(>  %s<1> atom<1>)" % (lhs,)), False)
  eq_(r.sample("(>= %s<1> atom<1>)" % (lhs,)), False)
  eq_(r.sample("( = %s<1> atom<1>)" % (lhs,)), False)

def checkGtAtom(lhs):
  r = get_ripl()
  eq_(r.sample("(<  %s<1> atom<0>)" % (lhs,)), True)
  eq_(r.sample("(<= %s<1> atom<0>)" % (lhs,)), True)
  eq_(r.sample("(>  %s<1> atom<0>)" % (lhs,)), False)
  eq_(r.sample("(>= %s<1> atom<0>)" % (lhs,)), False)
  eq_(r.sample("( = %s<1> atom<0>)" % (lhs,)), False)
