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

# Temporary
# Eventually this functionality should be part of the stack, perhaps a simple method 
# ripl.render(options)
#
# Currently only works in Puma
#
# Need graphviz installed (apt-get install graphviz)
#
# To render a new program, mimic renderTrickCoin

from subprocess import call
from venture.shortcuts import *

def RIPL():
  return make_church_prime_ripl()

def renderDot(dot,dirpath,i,fmt,colorIgnored):
  name = "dot%d" % i
  mkdir_cmd = "mkdir -p " + dirpath
  print mkdir_cmd
  call(mkdir_cmd,shell=True)
  dname = dirpath + "/" + name + ".dot"
  oname = dirpath + "/" + name + "." + fmt
  f = open(dname,"w")
  f.write(dot)
  f.close()
  cmd = ["dot", "-T" + fmt, dname, "-o", oname]
  print cmd
  call(cmd)

def renderRIPL(ripl,dirpath,fmt="svg",colorIgnored = False):
  dots = ripl.sivm.core_sivm.engine.getDistinguishedTrace().dot_trace(colorIgnored)
  i = 0
  for dot in dots:
    print "---dot---"
    renderDot(dot,dirpath,i,fmt,colorIgnored)
    i += 1
  
def renderTrickCoin():
  ripl = RIPL()
  ripl.assume("coin_is_tricky","(bernoulli 0.1)",label="istricky")
  ripl.assume("weight","(if coin_is_tricky (beta 1.0 1.0) 0.5)")
  ripl.observe("(bernoulli weight)","true")

  renderRIPL(ripl,"graphs/trickycoin")

renderTrickCoin()
