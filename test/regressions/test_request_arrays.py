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

def testRequestArrays():
  # ESRs should work even if the expressions being requested include
  # things like arrays (which are otherwise at risk of being treated
  # like evaluation structure).
  r = get_ripl()
  eq_([1.0, 2.0], r.sample("((lambda (obj) obj) (array 1 2))"))
  eq_([1.0, 2.0], r.sample("((mem (lambda (obj) obj)) (array 1 2))"))
  eq_([[1.0, 2.0]], r.sample("(mapv (lambda (obj) obj) (array (array 1 2)))"))
  eq_([[1.0, 2.0]], r.sample("(imapv (lambda (i obj) obj) (array (array 1 2)))"))
  eq_([1.0, 2.0], r.sample("(apply (lambda (obj) obj) (array (array 1 2)))"))
  eq_(2.0, r.sample("(eval (array (lambda (obj) obj) 2) (get_current_environment))"))
