# Copyright (c) 2013, 2014 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

import itertools

from nose import SkipTest
from nose.plugins.attrib import attr

from venture.test.config import default_num_transitions_per_sample
from venture.test.config import get_ripl
from venture.test.config import on_inf_prim

@attr("slow")
@on_inf_prim("mh")
def testGoldwater1():
  """Fairly complicated program. Just checks to make sure it runs without crashing."""
  raise SkipTest("This test blocked the inference quality suite for 9 hours once.  Issue: https://app.asana.com/0/11127829865276/12392223521813")
  ripl = get_ripl()

  brent = ["catanddog", "dogandcat", "birdandcat","dogandbird","birdcatdog"]

  N = default_num_transitions_per_sample()

  alphabet = "".join(set("".join(list(itertools.chain.from_iterable(brent)))))
  d = {}
  for i in xrange(len(alphabet)): d[alphabet[i]] = i

  ripl.assume("parameter_for_dirichlet","(if (flip) (normal 10 1) (gamma 1 1))")
  ripl.assume("alphabet_length", str(len(alphabet)))

  ripl.assume("sample_phone", "((if (flip) make_sym_dir_mult make_uc_sym_dir_mult) parameter_for_dirichlet alphabet_length)")
  # TODO What is the second parameter to make_crp supposed to be?
  # This line used to say "((if (flip) make_crp make_crp) (gamma 1.0 1.0) (uniform_continuous 0.001 0.01))"
  ripl.assume("sample_word_id", "((if (flip) make_crp make_crp) (gamma 1.0 1.0))")

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
      ripl.observe("(noisy_true (eq (sample_symbol %d %d) atom<%d>) noise)" %(i, j,d[str(brent[i][j])]), "true")

  ripl.infer(N) # TODO Make this an actual inference quality test.
