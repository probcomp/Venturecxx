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

from nose import SkipTest
from nose.tools import eq_
from venture.test.config import get_ripl, on_inf_prim

@on_inf_prim("none")
def testQuoteSmoke1():
  eq_(get_ripl().predict("(quote foo)"), "foo")

@on_inf_prim("none")
def testQuoteSmoke2():
  assert get_ripl().predict("(is_symbol (quote foo))")

@on_inf_prim("none")
def testQuoteSmoke3():
  assert get_ripl().predict("(is_array (quote (foo bar)))")

@on_inf_prim("none")
def testQuoteSmoke4():
  eq_(get_ripl().predict("(lookup (quote (foo bar)) 0)"), "foo")

@on_inf_prim("none")
def testQuoteIf():
  "Quote should suppress macroexpansion"
  raise SkipTest("This fails because the stack's \"desugaring\" is applied even to quoted expressions.  Oops.  Issue: https://app.asana.com/0/9277419963067/10442847514597")
  eq_(get_ripl().predict("(lookup (quote (if (flip) 0 1)) 0)"), "if")
