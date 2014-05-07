# Copyright (c) 2013, MIT Probabilistic Computing Project.
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
# You should have received a copy of the GNU General Public License along with Venture.  If not, see <http://www.gnu.org/licenses/>.
import unittest
from venture.shortcuts import make_church_prime_ripl
from nose.tools import eq_
 
def testBulkObserve1():
  ripl = make_church_prime_ripl()
  ripl.bulk_observe_proc("normal",[([0,5],11),([2,8],22),([3,10],33)],label="pid")
  ripl.infer(100)
  eq_(ripl.report("pid_0"),11)
  eq_(ripl.report("pid_1"),22)
  eq_(ripl.report("pid_2"),33)
  eq_(len(ripl.list_directives()),3)
