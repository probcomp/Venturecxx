# Copyright (c) 2014 -- 2018 MIT Probabilistic Computing Project.
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

from venture.test.config import get_ripl

def prep_ripl():
    ripl = get_ripl(seed=42)
    ripl.set_mode('venture_script')
    program = '''
        assume x = normal(0, 1);
        assume y = normal(x, 1);


        define resimulation_mh_with_infer  = () -> {
            infer resimulation_mh(default, one, 10)
        };

        define resimulation_mh_without_infer  = () -> {
            resimulation_mh(default, one, 10)
        };

        observe y = 2;
    '''
    ripl.execute_program(program)
    return ripl

def test_smoke():
    """Ensure with can run infer inside a function."""
    ripl = prep_ripl()
    ripl.execute_program('resimulation_mh_with_infer()')

def test_assert_infer_nullop():
    """ Ensure the same result is produced with and without infer keyword."""
    ripl1 = prep_ripl()
    ripl1.execute_program('resimulation_mh_with_infer()')
    y1 = ripl1.sample('y')
    ripl2 = prep_ripl()
    ripl2.execute_program('resimulation_mh_without_infer()')
    y2 = ripl2.sample('y')
    assert y1 == y2
