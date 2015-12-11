# Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
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

import os

from nose.plugins.attrib import attr

from venture.test.config import gen_on_inf_prim
from venture.test.config import get_ripl
import venture.test.timing as timing

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
lda_path = os.path.join(root, "examples", "lda.vnt")

def lda_ripl(n_topics = 4, vocab_size = 5, n_docs = 8, n_words_per_doc = 8):
    r = get_ripl()
    r.execute_program_from_file(lda_path)
    r.infer("(model %d %d)" % (n_topics, vocab_size))
    r.infer("(data %d %d)" % (n_docs, n_words_per_doc))
    return r

def sweep(ripl):
    get_entropy_info = ripl.sivm.core_sivm.engine.get_entropy_info
    # if #unconstrainted_random_choices stays fixed after infer(step)
    # then we do #iterations=#u_r_c. if #u_r_c grows after infer, we do
    # another step (with larger stepsize) and repeat.
    iters_done = 0
    while True:
        num_choices = get_entropy_info()['unconstrained_random_choices']
        if iters_done >= num_choices:
            break
        step = num_choices - iters_done
        ripl.infer("(mh default one %d)" % (step,))
        iters_done += step

@attr('slow')
@gen_on_inf_prim('mh')
def test_time_vs_dimension():
    for d in ["n_topics", "vocab_size", "n_docs", "n_words_per_doc"]:
        yield check_time_vs_dimension, d

def check_time_vs_dimension(dimension):
    def prep(n):
        kwargs = {dimension: n}
        r = lda_ripl(**kwargs)
        def doit():
            for _ in range(10):
                sweep(r)
        return doit

    # TODO Should the time per sweep be linear in the number of
    # topics?  I can see it growing as the probability of having to
    # create or destroy a topic rises, and as the cost of sampling
    # from the topic multinomial rises, but linear?  In practice, it
    # does increase, but slowly: from ~4s for 1 topic to ~6.5s for 46.

    # TODO Should the time per sweep be linear in the size of the
    # vocabulary?  In practice, it does increase, but very slowly:
    # from ~4s for 1 word to ~4.8s for 46.  This could also be random
    # noise.

    # n_docs and n_words_per_doc produce much more strikingly linear
    # runtimes, because they both increase the number of random
    # choices over which to infer.
    timing.assertLinearTime(prep, verbose=False)
