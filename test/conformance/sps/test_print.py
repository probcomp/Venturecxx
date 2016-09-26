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

from re import search

from nose.tools import eq_

from venture.test.config import broken_in
from venture.test.config import capture_output
from venture.test.config import get_ripl
from venture.test.config import on_inf_prim

def extract_integer(captured):
  'Extract the Venture integer from a captured print'
  res = search('VentureInteger\((.*)\)', captured) #pylint: disable=W1401
  return int(res.group(1))

def clear_Puma_warning(ripl):
  # Make the "using from Python" warning happen, so it's not in the
  # captured output for subsequent uses.
  capture_output(ripl, '(sample (debug "x" 1))')

@on_inf_prim("none")
def test_print1():
  # Make sure that debug prints the correct values by intercepting output
  ripl = get_ripl()
  clear_Puma_warning(ripl)
  x = ripl.assume('x', '(uniform_discrete 1 10)')
  y = ripl.assume('y', '(uniform_discrete 1 10)')
  program = ('''(sample (+ (debug "x" x) (debug "y" y)))''')
  res, captured = capture_output(ripl, program)
  res_value = res[0]['value']['value']
  captured_x, captured_y = map(extract_integer, captured.splitlines())
  eq_(x, captured_x)
  eq_(y, captured_y)
  eq_(res_value, captured_x + captured_y)

@on_inf_prim("none")
def test_print2():
  # Another test for consistency by intercepting output
  ripl = get_ripl()
  clear_Puma_warning(ripl)
  program = '''(sample (+ (debug "x" (uniform_discrete 1 10))
                          (debug "y" (uniform_discrete 1 10))))'''
  res, captured = capture_output(ripl, program)
  res_value = res[0]['value']['value']
  captured_values = map(extract_integer, captured.splitlines())
  eq_(res_value, sum(captured_values))
