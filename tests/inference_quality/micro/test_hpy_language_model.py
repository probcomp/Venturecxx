from venture.shortcuts import *
from stat_helpers import *
from test_globals import N, globalKernel

def RIPL(): return make_lite_church_prime_ripl()

def testHPYLanguageModel1(N):
  """Nice model from http://www.cs.berkeley.edu/~jordan/papers/teh-jordan-bnp.pdf.
     Checks that it learns that 1 follows 0"""
  ripl = RIPL()
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
  (atom_eq
    ((G (list atom<%d>)))
    atom<%d>)
  0.001)
""" % (atoms[i-1],atoms[i]), "true")

  ripl.predict("((G (list atom<0>)))",label="pid")

  predictions = collectSamples(ripl,"pid",N)
  ans = [(0,0.03), (1,0.88), (2,0.03), (3,0.03), (4,0.03)]
  return reportKnownDiscrete("testHPYLanguageModel1 (approximate)", ans, predictions)
