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

from nose.tools import eq_

from venture.test.config import get_ripl
from venture.parser import ast
import venture.value.dicts as e

def mk_my_scanner():
    def doit(char):
        if char in [" ", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]:
            return (False, None)
        else:
            return (True, ast.Located([0, 0], e.number(9)))
    return doit

def testSubscannerSmoke():
    r = get_ripl()
    r.set_mode("venture_script")
    r.register_language("troll", mk_my_scanner)
    eq_(10, r.evaluate("1 + @{troll 42}"))
    eq_(10, r.evaluate("1 + @{troll 27 }"))
    eq_(10, r.evaluate("1 + @{troll 4 3 3}"))
