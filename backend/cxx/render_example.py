from subprocess import call
from venture.shortcuts import *

def RIPL():
  return make_church_prime_ripl()

def renderDot(dot,dirpath,i):
  name = "dot%d" % i
  dname = dirpath + "/" + name + ".dot"
  oname = dirpath + "/" + name + ".svg"
  f = open(dname,"w")
  f.write(dot)
  f.close()
  cmd = ["dot", "-Tsvg", dname, "-o", oname]
  call(cmd)
  print "written to file: " + oname

def renderRIPL(ripl,dirpath):
  dots = ripl.sivm.core_sivm.engine.trace.dot_trace()
  i = 0
  for dot in dots:
    print "---dot---"
    print dot
    renderDot(dot,dirpath,i)
    i += 1
  
def renderTrickCoin():
  ripl = RIPL()
  ripl.assume("coin_is_tricky","(bernoulli 0.1)",label="istricky")
  ripl.assume("weight","(branch_exp coin_is_tricky (quote (beta 1.0 1.0)) (quote 0.5))")
  ripl.observe("(bernoulli weight)","true")

  renderRIPL(ripl,"graphs/trickycoin1")
  tricky = ripl.report("istricky")
  while ripl.report("istricky") == tricky:
    ripl.infer(10)

  renderRIPL(ripl,"graphs/trickycoin2")


 
