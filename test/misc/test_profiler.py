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

from venture.test.config import broken_in
from venture.test.config import get_ripl
from venture.test.config import on_inf_prim

@on_inf_prim("none")
@broken_in("puma", "Puma does not support proposal profiling.")
def testProfilerSmoke():
  ripl = get_ripl()
  ripl.execute_program("""
    [assume tricky (tag (quote tricky) 0 (flip 0.5))]
    [assume weight (if tricky (uniform_continuous 0 1) 0.5)]
    [assume coin (lambda () (flip weight))]
    [observe (coin) true]
    [observe (coin) true]
    [observe (coin) true]
  """)

  ripl.profiler_enable()
  ripl.infer('(resimulation_mh default one 10)')
  ripl.infer("(gibbs 'tricky one 1)")

  data = ripl.profile_data()

  assert len(data) == 11
