from venture.test.stats import *
from testconfig import config

def testIf1():
  "This caused an earlier CXX implementation to crash"
  ripl = config["get_ripl"]()
  ripl.assume('IF', '(lambda () branch)')
  ripl.assume('IF2', '(branch (bernoulli 0.5) IF IF)')
  ripl.predict('(IF2 (bernoulli 0.5) IF IF)')
  ripl.infer(10)

def testIf2():
  "More extended version of testIf1"
  ripl = config["get_ripl"]()
  ripl.assume('if1', '(branch (bernoulli 0.5) (lambda () branch) (lambda () branch))')
  ripl.assume('if2', '(branch (bernoulli 0.5) (lambda () if1) (lambda () if1))')
  ripl.assume('if3', '(branch (bernoulli 0.5) (lambda () if2) (lambda () if2))')
  ripl.assume('if4', '(branch (bernoulli 0.5) (lambda () if3) (lambda () if3))')
  ripl.infer(20)
