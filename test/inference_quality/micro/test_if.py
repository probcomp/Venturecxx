from venture.shortcuts import *
from stat_helpers import *
from test_globals import N, globalKernel

def RIPL(): return make_lite_church_prime_ripl()

def testIf1():
  ripl = RIPL()
  ripl.assume('IF', '(lambda () branch)')
  ripl.assume('IF2', '(branch (bernoulli 0.5) IF IF)')
  ripl.predict('(IF2 (bernoulli 0.5) IF IF)')
  ripl.infer(N/10)
  return reportPassage("TestIf1")

def testIf2():
  ripl = RIPL()
  ripl.assume('if1', '(branch (bernoulli 0.5) (lambda () branch) (lambda () branch))')
  ripl.assume('if2', '(branch (bernoulli 0.5) (lambda () if1) (lambda () if1))')
  ripl.assume('if3', '(branch (bernoulli 0.5) (lambda () if2) (lambda () if2))')
  ripl.assume('if4', '(branch (bernoulli 0.5) (lambda () if3) (lambda () if3))')
  ripl.infer(N/10)
  return reportPassage("TestIf2")
