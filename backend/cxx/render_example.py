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

def renderSprinkler():
  ripl = RIPL()
  ripl.assume("rain","(bernoulli 0.2)")
  ripl.assume("sprinkler","""
(tabular_cpt (make_vector rain) 
  (make_map (list true false) (list (make_vector 0.01 0.99) (make_vector 0.4 0.6)))
)
""")
  ripl.assume("grassWet","""
(tabular_cpt (make_vector rain sprinkler)
  (make_map (list (make_vector true true) (make_vector true false) (make_vector false true) (make_vector false false))
            (list (make_vector 0.99 0.01) (make_vector 0.8 0.2) (make_vector 0.9 0.1) (make_vector 0.00001 0.99999))))
""")

  sivm.observe("grassWet","true")

  renderRIPL(ripl,"graphs/sprinkler")



 
def renderSprinkler2():
  ripl = RIPL()
  ripl.assume("rain","(bernoulli 0.2)")
  ripl.assume("sprinkler","(bernoulli (branch_exp rain 0.01 0.4))")
  ripl.assume("grassWet","""
(bernoulli (branch_exp rain 
(branch_exp sprinkler 0.99 0.8)
(branch_exp sprinkler 0.9 0.00001)))
""")
  ripl.observe("grassWet", "true")
  renderRIPL(ripl,"graphs/sprinkler")

def renderPYMem():
  ripl = RIPL()
  ripl.assume("pymem","""
(lambda (alpha d base_dist)
  ((lambda (augmented_proc crp)
     (lambda () (augmented_proc (crp))))
   (mem (lambda (table) (base_dist)))
   (make_crp alpha d)))
""")

  ripl.assume("base_dist","(lambda () (normal 0.0 1.0))")

  ripl.assume("f","(pymem 1.0 0.0 base_dist)")
  ripl.predict("(f)")
  ripl.predict("(f)")
#  ripl.predict("(f)")
  renderRIPL(ripl,"graphs/pymem")
