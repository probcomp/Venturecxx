from venture.test.stats import *
from testconfig import config

def testGoldwater1():
  """Fairly complicated program. Just checks to make sure it runs without crashing."""
  get_ripl()

  brent = ["catanddog", "dogandcat", "birdandcat","dogandbird","birdcatdog"]

  N = int(config["num_transitions_per_sample"])
  
  parameter_for_dirichlet = 1

  alphabet = "".join(set("".join(list(itertools.chain.from_iterable(brent)))))
  d = {}
  for i in xrange(len(alphabet)): d[alphabet[i]] = i

  ripl.assume("parameter_for_dirichlet","(if (flip) (normal 10 1) (gamma 1 1))")
  ripl.assume("alphabet_length", str(len(alphabet)))

  ripl.assume("sample_phone", "((if (flip) make_sym_dir_mult make_uc_sym_dir_mult) parameter_for_dirichlet alphabet_length)")
  ripl.assume("sample_word_id", "((if (flip) make_crp make_crp) (gamma 1.0 1.0) (uniform_continuous 0.001 0.01))")

  ripl.assume("sample_letter_in_word", """
(mem (lambda (word_id pos)
  (sample_phone)))
""")
#7
  ripl.assume("is_end", """
(mem (lambda (word_id pos)
  (flip .3)))
""")

  ripl.assume("get_word_id","""
(mem (lambda (sentence sentence_pos)
  (if (= sentence_pos 0)
      (sample_word_id)
      (if (is_end (get_word_id sentence (- sentence_pos 1))
                  (get_pos sentence (- sentence_pos 1)))
          (sample_word_id)
          (get_word_id sentence (- sentence_pos 1))))))
""")

  ripl.assume("get_pos","""
(mem (lambda (sentence sentence_pos)
  (if (= sentence_pos 0)
      0
      (if (is_end (get_word_id sentence (- sentence_pos 1))
                  (get_pos sentence (- sentence_pos 1)))
        0
        (+ (get_pos sentence (- sentence_pos 1)) 1)))))
""")

  ripl.assume("sample_symbol","""
(mem (lambda (sentence sentence_pos)
  (sample_letter_in_word (get_word_id sentence sentence_pos) (get_pos sentence sentence_pos))))
""")

  ripl.assume("noise","(gamma 1 1)")
  ripl.assume("noisy_true","(lambda (pred noise) (flip (if pred 1.0 noise)))")


  for i in range(len(brent)): #for each sentence
    for j in range(len(brent[i])): #for each letter
      ripl.predict("(sample_symbol %d %d)" %(i, j))
      ripl.observe("(noisy_true (atom_eq (sample_symbol %d %d) atom<%d>) noise)" %(i, j,d[str(brent[i][j])]), "true")

  ripl.infer(N * 10) # TODO Make this an actual inference quality test.
