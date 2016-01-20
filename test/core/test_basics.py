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

from numbers import Number

from nose.tools import eq_

from venture.ripl import Ripl
from venture.test.config import collectSamples
from venture.test.config import get_ripl
from venture.test.config import on_inf_prim
from venture.test.stats import reportKnownDiscrete
from venture.test.stats import statisticalTest

@on_inf_prim("none")
def testRIPL():
  assert isinstance(get_ripl(), Ripl)

@on_inf_prim("none")
def testConstant():
  eq_(1, get_ripl().predict(1))

@on_inf_prim("none")
def testLambda():
  eq_(2, get_ripl().predict("((lambda (x) x) 2)"))

@on_inf_prim("none")
def testTriviality1():
  eq_(4, get_ripl().predict("(+ 2 2)"))

@on_inf_prim("none")
def testTriviality2():
  eq_(2, get_ripl().predict("(- 4 2)"))

@on_inf_prim("none")
def testIf1():
  eq_(2, get_ripl().predict("(if true 2 3)"))

@on_inf_prim("none")
def testIf2():
  eq_(3, get_ripl().predict("(if false 2 3)"))

@on_inf_prim("none")
def testIf3():
  ripl = get_ripl()
  ripl.assume("z", "1")
  ripl.assume("y", "2")
  eq_(1, ripl.predict("(if true z y)"))

@on_inf_prim("none")
def testFlip1():
  assert isinstance(get_ripl().predict("(bernoulli 0.5)"), Number)

@statisticalTest
def testFlip2():
  ripl = get_ripl()
  ripl.predict("(bernoulli 0.5)",label="pid")
  predictions = collectSamples(ripl, "pid")
  return reportKnownDiscrete([[True, 0.5], [False, 0.5]], predictions)

@on_inf_prim("none")
def testAtom():
  assert get_ripl().predict("(is_atom atom<1>)")

def testString():
  eq_("foo", get_ripl().evaluate('"foo"'))

def testModelString():
  eq_("foo", get_ripl().sample('"foo"'))
