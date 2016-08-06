# Copyright (c) 2016 MIT Probabilistic Computing Project.
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

from nose.tools import eq_
import numpy as np

from venture.test.config import broken_in
from venture.test.config import collectSamples
from venture.test.config import default_num_data
from venture.test.config import get_ripl
from venture.test.config import on_inf_prim
from venture.test.config import skipWhenDoingParticleGibbs
from venture.test.config import skipWhenRejectionSampling
from venture.test.stats import reportKnownGaussian
from venture.test.stats import statisticalTest

__author__ = 'ulli'

# Simple smoke test

@broken_in("puma", "Does not have refs: Issue #224.")
@on_inf_prim("none")
def test_compound_assume_smoke():
    smoke_prog ="""
    [assume a_ref (ref (uniform_discrete 2 3))]
    [assume b_ref (ref (uniform_discrete 3 4))]
    (assume_values (a b) (list a_ref b_ref))

    [assume l (list a_ref b_ref)]
    (assume_values (c d) l)

    (assume_values (u) (list (ref (uniform_discrete 20 21))))
    """

    ripl = get_ripl()
    ripl.execute_program(smoke_prog)

    assert ripl.sample("a") == 2, "compound assume does not work, first component"
    assert ripl.sample("b") == 3, "compound assume does not work, second component"

    assert ripl.sample("c") == 2, "compound assume does not work, first component, symbol instead of list"
    assert ripl.sample("d") == 3, "compound assume does not work, second component"

    assert ripl.sample("u") == 20, "compound assume does not work for a one-element-compound"

@broken_in("puma", "Does not have refs: Issue #224.")
@on_inf_prim("none")
def test_compound_assume_nonduplication():
    ripl = get_ripl()
    ripl.execute_program("""
(assume_values (a b)
  (if (flip) (list (ref 1) (ref 2)) (list (ref 2) (ref 1))))""")
    engine = ripl.sivm.core_sivm.engine
    eq_(engine.get_entropy_info()["unconstrained_random_choices"],1)
    for _ in range(30):
        ripl.infer("(mh default one 1)")
        assert ripl.sample("a") != ripl.sample("b")

# Testing observations

@broken_in("puma", "Does not have refs: Issue #224.")
@on_inf_prim("none")
def test_compound_assume_observations():
    obs_prog ="""
    [assume a_ref (ref (normal 0 1))]
    [assume b_ref (ref (normal 0 1))]
    [assume l (list a_ref b_ref)]
    (assume_values (a b) l)
    """

    ripl = get_ripl()

    ripl.execute_program(obs_prog)

    ripl.observe("(deref a_ref)", 1)

    assert ripl.sample("(deref a_ref)") == 1, "simple a_ref is not observed"
    assert ripl.sample("a") == 1, "first element compund is not observed"
    assert ripl.sample("(deref (first  l))") == 1, "first compound list item is not observed"
    assert ripl.sample("(deref (second l))") != 1, "confused second and first compound element"
    assert ripl.sample("(deref b_ref)") != 1, "confused second and first compound element"
    assert ripl.sample("b") != 1, "second element compound is confused with first"

    ripl.observe("b", 2)

    assert ripl.sample("b") == 2, "second element compound is not observed"
    assert ripl.sample("(deref a_ref)") == 1, "second observation made the first incorrect"
    assert ripl.sample("(deref (first  l))") == 1, "second observation made the first incorrect"
    assert ripl.sample("(deref (second l))") == 2, "deref of second list item is not observed"
    assert ripl.sample("(deref b_ref)") == 2, "deref of second ref is not observed"

# Testing inference

@broken_in("puma", "Does not have refs: Issue #224.")
@on_inf_prim("mh")
def test_compound_assume_inf_happening():
    inf_test_prog ="""
    [assume a_ref (tag (quote a_scope) 0 (ref (normal 0 10)))]
    [assume b_ref (tag (quote b_scope) 0 (ref (normal -10 10)))]
    [assume l (list a_ref b_ref)]
    (assume_values (a b) l)

    [assume obs_1 (lambda () (normal a 1))]
    [assume obs_2 (lambda () (normal b 1))]
    """

    ripl = get_ripl()
    ripl.execute_program(inf_test_prog)

    previous_value = ripl.sample("b")

    ripl.observe("(obs_1)", np.random.normal(5, 0.1))
    ripl.infer("(mh (quote a_scope) 0 50)")
    assert ripl.sample("b") == previous_value, "inferred to wrong part of the compound"

    ripl.observe("(obs_2)", np.random.normal(-15, 0.1))
    ripl.infer("(mh (quote b_scope) 0 50)")
    assert ripl.sample("b") != previous_value, "inferred for second part didn't work"

@broken_in("puma", "Does not have refs: Issue #224.")
@statisticalTest
@skipWhenDoingParticleGibbs("Issue #531")
def test_compound_assume_inf_first_element(seed):
    inf_test_prog ="""
    [assume a_ref (tag (quote a_scope) 0 (ref (normal 0 10)))]
    [assume b_ref (tag (quote b_scope) 0 (ref (normal -10 10)))]
    [assume l (list a_ref b_ref)]
    (assume_values (a b) l)

    [assume obs_1 (make_suff_stat_normal a 1)]
    [assume obs_2 (make_suff_stat_normal b 1)]
    """

    ripl = get_ripl(seed=seed)
    ripl.execute_program(inf_test_prog)

    for _ in range(default_num_data()):
        ripl.observe("(obs_1)", np.random.normal(5, 1))

    ripl.predict("(obs_1)", label="predictive")
    post_samples = collectSamples(ripl, "predictive")
    return reportKnownGaussian(5, 1, post_samples)

@broken_in("puma", "Does not have refs: Issue #224.")
@statisticalTest
@skipWhenRejectionSampling("Rejection takes too long to solve this")
@skipWhenDoingParticleGibbs("Issue #531")
def test_compound_assume_inf_second_element(seed):
    inf_test_prog ="""
    [assume a_ref (tag (quote a_scope) 0 (ref (normal 0 10)))]
    [assume b_ref (tag (quote b_scope) 0 (ref (normal -10 10)))]
    [assume l (list a_ref b_ref)]
    (assume_values (a b) l)

    [assume obs_1 (make_suff_stat_normal a 1)]
    [assume obs_2 (make_suff_stat_normal b 1)]
    """

    ripl = get_ripl(seed=seed)
    ripl.execute_program(inf_test_prog)

    for _ in range(default_num_data()):
        ripl.observe("(obs_1)", np.random.normal(5, 0.1))

    for _ in range(default_num_data()):
        ripl.observe("(obs_2)", np.random.normal(-15, 0.1))

    ripl.predict("(obs_2)", label="predictive")
    post_samples = collectSamples(ripl, "predictive")
    return reportKnownGaussian(-15, 1, post_samples)

@statisticalTest
@skipWhenDoingParticleGibbs("Issue #531")
def test_model_without_compound_assume(seed):
    inf_test_prog ="""
    [assume a (tag (quote a_scope) 0 (normal 0 10))]
    [assume b (tag (quote b_scope) 0 (normal -10 10))]
    [assume obs_1 (make_suff_stat_normal a 1)]
    [assume obs_2 (make_suff_stat_normal b 1)]
    """

    ripl = get_ripl(seed=seed)
    ripl.execute_program(inf_test_prog)

    for _ in range(default_num_data()):
        ripl.observe("(obs_1)", np.random.normal(5, 1))

    ripl.predict("(obs_1)", label="predictive")
    post_samples = collectSamples(ripl, "predictive")
    return reportKnownGaussian(5, 1, post_samples)
