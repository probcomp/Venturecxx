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

from nose.plugins.attrib import attr

from venture.test.config import get_ripl, on_inf_prim
import venture.test.timing as timing

@attr('slow')
@on_inf_prim("mh")
def test_double_recursion():
  def test(n):
    ripl = get_ripl()
    ripl.assume('a', '(normal 0 1)')
    ripl.assume('f', '''(mem (lambda (n)
         (if (= n 0) 0
             (+ a (f (- n 1)) (f (- n 1))))))''')
    ripl.predict('(f %d)' % n)
    ripl.infer(1) # Warm up the system s.t. subsequent timings are ok
    def thunk():
      ripl.infer(10)
    return thunk

  timing.assertLinearTime(test, verbose=True)
