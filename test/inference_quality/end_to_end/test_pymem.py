from venture.test.stats import statisticalTest, reportSameDiscrete, reportKnownDiscrete
from venture.test.config import get_ripl, collectSamples
from nose import SkipTest
from nose.plugins.attrib import attr

def loadPYMem(ripl):
  ripl.assume("pick_a_stick","""
(lambda (sticks k)
  (if (bernoulli (sticks k))
      k
      (pick_a_stick sticks (+ k 1))))
""")

  ripl.assume("make_sticks","""
(lambda (alpha d)
  ((lambda (sticks) (lambda () (pick_a_stick sticks 1)))
   (mem (lambda (k)
     (beta (- 1 d)
           (+ alpha (* k d)))))))
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
    for _ in range(counts[i]):
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

def predictHPY(topCollapsed,botCollapsed):
  ripl = get_ripl()
  loadHPYModel1(ripl,topCollapsed,botCollapsed)
  ripl.predict("(f)",label="pid")
  observeCategories(ripl,[2,2,5,1,0])
  return collectSamples(ripl,"pid")

@attr("slow")
def testHPYMem1():
  raise SkipTest("Crashes occasionally because flip gets asked to evaluate how likely it is to return False when p is 1.0.  Issue: https://app.asana.com/0/9277419963067/10386828313646")
  baseline = predictHPY(True, True)
  for topC in [True,False]:
    for botC in [True,False]:
      yield checkHPYMem1, baseline, topC, botC

@statisticalTest
def checkHPYMem1(baseline, topC, botC):
  data = predictHPY(topC, botC)
  return reportSameDiscrete(baseline, data)

####

@statisticalTest
def testHPYLanguageModel1():
  """Nice model from http://www.cs.berkeley.edu/~jordan/papers/teh-jordan-bnp.pdf.
     Checks that it learns that 1 follows 0"""
  ripl = get_ripl()

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

  atoms = [0, 1, 2, 3, 4] * 5

  for i in range(1,len(atoms)):
    ripl.observe("""
(noisy_true
  (eq
    ((G (list atom<%d>)))
    atom<%d>)
  0.001)
""" % (atoms[i-1],atoms[i]), "true")

  ripl.predict("((G (list atom<0>)))",label="pid")

  raise SkipTest("Skipping testHPYLanguageModel because it's slow and I don't how fast it is expected to converge.  Issue https://app.asana.com/0/9277419963067/9801332616429")
  predictions = collectSamples(ripl,"pid")
  ans = [(0,0.03), (1,0.88), (2,0.03), (3,0.03), (4,0.03)]
  return reportKnownDiscrete(ans, predictions)
