from venture.shortcuts import *
from stat_helpers import *
from test_globals import N, globalKernel

def RIPL(): return make_lite_church_prime_ripl()

# TODO this file is a chaotic dump from wstests


def loadPYMem(ripl):
  ripl.assume("pick_a_stick","""
(lambda (sticks k)
  (branch (bernoulli (sticks k))
    (lambda () k)
    (lambda () (pick_a_stick sticks (plus k 1)))))
""")

  ripl.assume("make_sticks","""
(lambda (alpha d)
  ((lambda (sticks) (lambda () (pick_a_stick sticks 1)))
   (mem (lambda (k)
     (beta (minus 1 d)
           (plus alpha (times k d)))))))
""")

  ripl.assume("u_pymem","""
(lambda (alpha d base_dist)
  ((lambda (augmented_proc py)
     (lambda () (augmented_proc (py))))
   (mem (lambda (stick_index) (base_dist)))
   (make_sticks alpha d)))
""")

  ripl.assume("pymem","""
(lambda (alpha d base_dist)
  ((lambda (augmented_proc crp)
     (lambda () (augmented_proc (crp))))
   (mem (lambda (table) (base_dist)))
   (make_crp alpha d)))
""")


def testDPMem1(N):
  ripl = RIPL()
  loadDPMem(ripl)

  ripl.assume("alpha","(uniform_continuous 0.1 20.0)")
  ripl.assume("base_dist","(lambda () (real (categorical 0.5 0.5)))")
  ripl.assume("f","(u_dpmem alpha base_dist)")

  ripl.predict("(f)")
  ripl.predict("(f)")
  ripl.observe("(normal (f) 1.0)",1.0)
  ripl.observe("(normal (f) 1.0)",1.0)
  ripl.observe("(normal (f) 1.0)",0.0)
  ripl.observe("(normal (f) 1.0)",0.0)
  ripl.infer(N)
  return reportPassage("TestDPMem1")

def observeCategories(ripl,counts):
  for i in range(len(counts)):
    for ct in range(counts[i]):
      ripl.observe("(flip (if (= (f) %d) 1.0 0.1))" % i,"true")

def testCRP1(N,isCollapsed):
  ripl = RIPL()
  loadPYMem(ripl)
  ripl.assume("alpha","(gamma 1.0 1.0)")
  ripl.assume("d","(uniform_continuous 0.0 0.1)")
  ripl.assume("base_dist","(lambda () (real (categorical 0.2 0.2 0.2 0.2 0.2)))")
  if isCollapsed: ripl.assume("f","(pymem alpha d base_dist)")
  else: ripl.assume("f","(u_pymem alpha d base_dist)")

  ripl.predict("(f)",label="pid")

  observeCategories(ripl,[2,2,5,1,0])

  predictions = collectSamples(ripl,"pid",N)
  ans = [(0,3), (1,3), (2,6), (3,2), (4,1)]
  return reportKnownDiscrete("TestCRP1 (not exact)", ans, predictions)

def loadHPY(ripl,topCollapsed,botCollapsed):
  loadPYMem(ripl)
  ripl.assume("alpha","(gamma 1.0 1.0)")
  ripl.assume("d","(uniform_continuous 0.0 0.1)")
  ripl.assume("base_dist","(lambda () (real (categorical 0.2 0.2 0.2 0.2 0.2)))")
  if topCollapsed: ripl.assume("intermediate_dist","(pymem alpha d base_dist)")
  else: ripl.assume("intermediate_dist","(u_pymem alpha d base_dist)")
  if botCollapsed: ripl.assume("f","(pymem alpha d intermediate_dist)")
  else: ripl.assume("f","(u_pymem alpha d intermediate_dist)")

def loadPY(ripl):
  loadPYMem(ripl)
  ripl.assume("alpha","(gamma 1.0 1.0)")
  ripl.assume("d","(uniform_continuous 0 0.0001)")
  ripl.assume("base_dist","(lambda () (real (categorical 0.2 0.2 0.2 0.2 0.2)))")
  ripl.assume("f","(u_pymem alpha d base_dist)")

def predictPY(N):
  ripl = RIPL()
  loadPY(ripl)
  ripl.predict("(f)",label="pid")
  observeCategories(ripl,[2,2,5,1,0])
  return collectSamples(ripl,"pid",N)

def predictHPY(N,topCollapsed,botCollapsed):
  ripl = RIPL()
  loadHPY(ripl,topCollapsed,botCollapsed)
  ripl.predict("(f)",label="pid")
  observeCategories(ripl,[2,2,5,1,0])
  return collectSamples(ripl,"pid",N)

def doTestHPYMem1(N):
  data = [countPredictions(predictHPY(N,top,bot), [0,1,2,3,4]) for top in [True,False] for bot in [True,False]]
  (chisq, pval) = stats.chi2_contingency(data)
  report = [
    "Expected: Samples from four equal distributions",
    "Observed:"]
  i = 0
  for top in ["Collapsed", "Uncollapsed"]:
    for bot in ["Collapsed", "Uncollapsed"]:
      report += "  (%s, %s): %s" % (top, bot, data[i])
      i += 1
  report += [
    "Chi^2   : " + str(chisq),
    "P value : " + str(pval)]
  return TestResult("TestHPYMem1", pval, "\n".join(report))

def testHPYMem1(N):
  if hasattr(stats, 'chi2_contingency'):
    return doTestHPYMem1(N)
  else:
    print "---TestHPYMem1 skipped for lack of scipy.stats.chi2_contingency"
    return reportPassage("TestHPYMem1")
