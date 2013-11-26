from subprocess import call
from venture.shortcuts import *

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
 
