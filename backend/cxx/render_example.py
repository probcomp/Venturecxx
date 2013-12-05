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
  dots = ripl.sivm.core_sivm.engine.trace.dot_trace(colorIgnored)
  i = 0
  for dot in dots:
    print "---dot---"
    renderDot(dot,dirpath,i,fmt,colorIgnored)
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

def renderCPYMem():
  ripl = RIPL()
  ripl.assume("pymem","""
(lambda (alpha d base_dist)
  ((lambda (augmented_proc crp)
     (lambda () (augmented_proc (crp))))
   (mem (lambda (table) (base_dist)))
   (make_crp alpha d)))
""")

  ripl.assume("f","(pymem 1.0 0.0 bernoulli)")
  ripl.predict("(f)")
  ripl.predict("(f)")
#  ripl.predict("(f)")
  renderRIPL(ripl,"graphs/cpymem")

def renderBPYMem():
  ripl = RIPL()
  ripl.assume("f","(pymem bernoulli 1.0 0.1)")
  ripl.predict("(f)")
  ripl.predict("(f)")
  ripl.predict("(f)")

  renderRIPL(ripl,"graphs/bpymem")


def renderERG1():
  ripl = RIPL()
  ripl.assume("x","(gamma 1.0 1.0)")
  ripl.assume("y","(branch_exp (< x 1) (quote (gamma x 2.0)) (quote (normal x 2.0)))")
  ripl.observe("(normal y 5.0)","10.0")

  renderRIPL(ripl,"graphs/erg1")


####################### Schematics

def renderERGtoDRG():
  ripl = RIPL()

  ripl.assume("x","(snormal 1.0)")
  ripl.observe("(snormal (branch_exp x (quote (snormal x)) (quote (snormal x))))", "10")

  renderRIPL(ripl,"pdf_graphs/erg_to_drg","pdf")
  renderRIPL(ripl,"graphs/erg_to_drg")

def renderRegenToEvalToRegen():
  ripl = RIPL()

  ripl.assume("x","(snormal 0.0)")
  ripl.assume("y","x")
  ripl.predict("(branch_exp x (quote (snormal y)) (quote 1))")

  renderRIPL(ripl,"pdf_graphs/regen_to_eval_to_regen","pdf")
  renderRIPL(ripl,"graphs/regen_to_eval_to_regen")

def renderAAABasicNoAAA():
  ripl = RIPL()

  ripl.assume("alpha","(snormal 100.0)")
  ripl.assume("f","(make_sym_dir_mult_reg alpha 2)")
  for i in range(8): ripl.observe("(f)","atom<1>")

  renderRIPL(ripl,"pdf_graphs/aaa_basic_no_aaa","pdf")
  renderRIPL(ripl,"graphs/aaa_basic_no_aaa")

def renderAAABasic():
  ripl = RIPL()

  ripl.assume("alpha","(snormal 100.0)")
  ripl.assume("f","(make_sym_dir_mult alpha 2)")
  for i in range(8): ripl.observe("(f)","atom<1>")

  renderRIPL(ripl,"pdf_graphs/aaa_basic_with_aaa","pdf")
  renderRIPL(ripl,"graphs/aaa_basic_with_aaa")

def renderAAAChallengeNoAAA():
  ripl = RIPL()

  ripl.assume("alpha","(snormal 100.0)")
  ripl.assume("f","(make_sym_dir_mult_reg alpha 2)")
  ripl.assume("g","f")
  for i in range(3): ripl.observe("(g)","atom<1>")
  ripl.predict("(branch_exp alpha (quote g) (quote g))")

  renderRIPL(ripl,"pdf_graphs/aaa_challenge_no_aaa","pdf")
  renderRIPL(ripl,"graphs/aaa_challenge_no_aaa")

def renderAAAChallenge():
  ripl = RIPL()

  ripl.assume("alpha","(snormal 100.0)")
  ripl.assume("f","(make_sym_dir_mult alpha 2)")
  ripl.assume("g","f")
  for i in range(3): ripl.observe("(g)","atom<1>")
  ripl.predict("(branch_exp alpha (quote g) (quote g))")

  renderRIPL(ripl,"pdf_graphs/aaa_challenge_with_aaa","pdf")
  renderRIPL(ripl,"graphs/aaa_challenge_with_aaa")

def renderPartition():
  ripl = RIPL()
  ripl.assume("x","(snormal 0)")
  ripl.assume("y","(snormal x)")
  ripl.assume("w","(snormal (branch_exp y (quote (snormal 0.0)) (quote 5)) 1.0)")
  ripl.predict("(snormal w)")
              
  renderRIPL(ripl,"pdf_graphs/partition","pdf",colorIgnored=True)
  renderRIPL(ripl,"graphs/partition",colorIgnored=True)

def render():
  ripl = RIPL()
  ripl.assume("x","0")
  ripl.assume("y","(snormal x)")
  ripl.assume("w","(snormal (branch_exp y (quote (snormal 0.0)) (quote 5)) 1.0)")
  ripl.predict("(snormal w)")
              
  renderRIPL(ripl,"pdf_graphs/partition","pdf",colorIgnored=True)
  renderRIPL(ripl,"graphs/partition",colorIgnored=True)


#####################
def renderAllSchematics():
  renderERGtoDRG()
  renderRegenToEvalToRegen()
  renderAAABasicNoAAA()
  renderAAABasic()
  renderAAAChallengeNoAAA()
  renderAAAChallenge()
  renderPartition()
