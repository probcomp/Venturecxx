from venture.test.stats import *
from testconfig import config

def testIf1():
  "This caused an earlier CXX implementation to crash"
  ripl = config["get_ripl"]()
  ripl.assume('IF', '(quote branch)')
  ripl.assume('IF2', '(branch (bernoulli 0.5) IF IF)')
  ripl.predict('(IF2 (bernoulli 0.5) IF IF)')
  ripl.infer(10)
  return reportPassage("TestIf1")

def testIf2():
  "More extended version of testIf1"
  ripl = config["get_ripl"]()
  ripl.assume('if1', '(if (bernoulli 0.5) branch branch)')
  ripl.assume('if2', '(if (bernoulli 0.5) if1 if1)')
  ripl.assume('if3', '(if (bernoulli 0.5) if2 if2)')
  ripl.assume('if4', '(if (bernoulli 0.5) if3 if3)')
  ripl.infer(20)
  return reportPassage("TestIf2")
