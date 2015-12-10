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

from nose.tools import assert_raises

from venture.test.config import get_ripl
from venture.exception import VentureException

def test_timer1():
  ripl = get_ripl()
  ripl.infer('(call_back timer_start)')
  ripl.infer('(call_back timer_pause)')
  with assert_raises(VentureException):
    ripl.infer('(call_back timer_pause)')

def test_timer2():
  ripl = get_ripl()
  ripl.infer('(call_back timer_start)')
  ripl.infer('(call_back timer_pause)')
  ripl.infer('(call_back timer_resume)')
  with assert_raises(VentureException):
    ripl.infer('(call_back timer_resume)')

def test_timer3():
  ripl = get_ripl()
  with assert_raises(VentureException):
    ripl.infer('(call_back timer_time)')

def test_timer4():
  ripl = get_ripl()
  ripl.infer('(call_back timer_start)')
  ripl.infer('(call_back timer_time)')
