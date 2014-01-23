from venture.test.stats import *
from testconfig import config

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

  ripl.assume("uc_pymem","""
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

def observeCategories(ripl,counts):
  for i in range(len(counts)):
    for ct in range(counts[i]):
      ripl.observe("(flip (if (= (f) %d) 1.0 0.1))" % i,"true")

def loadHPYModel1(ripl,topCollapsed,botCollapsed):
  loadPYMem(ripl)
  ripl.assume("alpha","(gamma 1.0 1.0)")
  ripl.assume("d","(uniform_continuous 0.0 0.1)")
  ripl.assume("base_dist","""
(lambda () 
  (categorical (simplex 0.2 0.2 0.2 0.2 0.2)
               (array 0 1 2 3 4)))
""")
  if topCollapsed: ripl.assume("intermediate_dist","(pymem alpha d base_dist)")
  else: ripl.assume("intermediate_dist","(uc_pymem alpha d base_dist)")
  if botCollapsed: ripl.assume("f","(pymem alpha d intermediate_dist)")
  else: ripl.assume("f","(uc_pymem alpha d intermediate_dist)")

def predictHPY(N,topCollapsed,botCollapsed):
  ripl = RIPL()
  loadHPY(ripl,topCollapsed,botCollapsed)
  ripl.predict("(f)",label="pid")
  observeCategories(ripl,[2,2,5,1,0])
  return collectSamples(ripl,"pid",N)

def testHPYMem1():
  from nose import SkipTest
  raise SkipTest("Skipping testHPYMem1: no p-value test for comparing empirical distributions")
  data = [countPredictions(predictHPY(N,top,bot), [0,1,2,3,4]) for top in [True,False] for bot in [True,False]]
  return reportKnownEqualDistributions(data)

####

def testHPYLanguageModel1():
  """Nice model from http://www.cs.berkeley.edu/~jordan/papers/teh-jordan-bnp.pdf.
     Checks that it learns that 1 follows 0"""
  N = config["num_samples"]
  ripl = config["get_ripl"]()

  loadPYMem(ripl)

  # 5 letters for now
  ripl.assume("G_init","(make_sym_dir_mult 0.5 5)")

  # globally shared parameters for now
  ripl.assume("alpha","(gamma 1.0 1.0)")
  ripl.assume("d","(uniform_continuous 0.0 0.01)")

  # G(letter1 letter2 letter3) ~ pymem(alpha,d,G(letter2 letter3))
  ripl.assume("G","""
(mem (lambda (context)
  (if (is_pair context)
      (pymem alpha d (G (rest context)))
      (pymem alpha d G_init))))
""")

  ripl.assume("noisy_true","(lambda (pred noise) (flip (if pred 1.0 noise)))")

  atoms = [0, 1, 2, 3, 4] * 5;

  for i in range(1,len(atoms)):
    ripl.observe("""
(noisy_true
  (eq
    ((G (list atom<%d>)))
    atom<%d>)
  0.001)
""" % (atoms[i-1],atoms[i]), "true")

  ripl.predict("((G (list atom<0>)))",label="pid")

  predictions = collectSamples(ripl,"pid",N)
  ans = [(0,0.03), (1,0.88), (2,0.03), (3,0.03), (4,0.03)]
  return reportKnownDiscrete("testHPYLanguageModel1 (approximate)", ans, predictions)
