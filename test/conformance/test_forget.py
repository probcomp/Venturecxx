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

from venture.test.config import get_ripl, on_inf_prim

@on_inf_prim("none")
def testForgetSmoke1():
  ripl = get_ripl()
  for i in range(10):
    pid = "pid%d" % i
    ripl.predict("(flip)",label=pid)
    ripl.forget(pid)

@on_inf_prim("none")
def testForgetSmoke2():
  ripl = get_ripl()
  for i in range(10):
    pid = "pid%d" % i
    ripl.predict("(flip)",label=pid)

  for i in range(10):
    pid = "pid%d" % i
    ripl.forget(pid)

@on_inf_prim("mh")
def testForgetContinuousInference3():
  ripl = get_ripl()
  for i in range(10):
    pid = "pid%d" % i
    ripl.predict("(flip)",label=pid)
    ripl.infer(5)
    
  for i in reversed(range(10)):
    pid = "pid%d" % i
    ripl.forget(pid)
    ripl.infer(5)

@on_inf_prim("mh")
def testForgetContinuousInference4():
  ripl = get_ripl()
  for i in range(10):
    pid = "pid%d" % i
    ripl.observe("(flip)","true",label=pid)
    ripl.infer(5)
    
  for i in range(10):
    pid = "pid%d" % i
    ripl.forget(pid)
    ripl.infer(5)

  for i in range(10,20):
    pid = "pid%d" % i
    ripl.observe("(flip)","true",label=pid)
    ripl.infer(5)
    
  for i in reversed(range(10,20)):
    pid = "pid%d" % i
    ripl.forget(pid)
    ripl.infer(5)
            
