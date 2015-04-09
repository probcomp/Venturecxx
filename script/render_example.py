# Copyright (c) 2013, 2014 MIT Probabilistic Computing Project.
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

from subprocess import call
from venture.shortcuts import make_church_prime_ripl

def RIPL():
  return make_church_prime_ripl()

def renderDot(dot,i):
  name = "dot%d" % i
  dname = name + ".dot"
  oname = name + ".svg"
  f = open(dname,"w")
  f.write(dot)
  f.close()
  cmd = ["dot", "-Tsvg", dname, "-o", oname]
  call(cmd)
  print "written to file: " + oname

def testRender1():
  ripl = RIPL()
  ripl.assume("f","(lambda (p) (bernoulli p))")
  ripl.predict("(if (f 0.5) (normal 0.0 1.0) (gamma 1.0 1.0))")

  sivm = ripl.sivm.core_sivm.engine
  dots = sivm.trace.dot_trace()
  i = 0
  for dot in dots:
    print "---dot---"
    print dot
    renderDot(dot,i)
    i += 1
 
