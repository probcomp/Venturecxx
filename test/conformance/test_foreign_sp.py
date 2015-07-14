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

from venture.test.config import get_ripl, defaultInfer, skipWhenInParallel, collectSamples
from venture.test.stats import statisticalTest, reportKnownDiscrete
from venture.lite import builtin
from venture.lite.builtin import binaryNum

import numpy as np
from nose.tools import assert_raises_regexp

def test_foreign_aaa():
    builtins = builtin.builtInSPs()
    ripl = get_ripl()
    ripl.bind_foreign_sp("test_sym_dir_mult", builtins["make_sym_dir_mult"])

    ripl.assume("f", "(test_sym_dir_mult 1 1)")
    assert ripl.sample("f")["counts"] == [0]

    ripl.observe("(f)", "atom<0>")
    assert ripl.sample("f")["counts"] == [1]

    ripl.infer(defaultInfer())
    assert ripl.sample("f")["counts"] == [1]

@skipWhenInParallel("Calling into Lite from Puma is not thread-safe. Issue: https://app.asana.com/0/11127829865276/15184529953373")
def test_foreign_aaa_resampled():
    builtins = builtin.builtInSPs()
    ripl = get_ripl()
    ripl.bind_foreign_sp("test_sym_dir_mult", builtins["make_sym_dir_mult"])

    ripl.assume("a", "(gamma 1 1)")
    ripl.assume("f", "(test_sym_dir_mult a 1)")
    assert ripl.sample("f")["counts"] == [0]

    ripl.observe("(f)", "atom<0>")
    assert ripl.sample("f")["counts"] == [1]

    ripl.infer(defaultInfer())
    assert ripl.sample("f")["counts"] == [1]

@skipWhenInParallel("Calling into Lite from Puma is not thread-safe. Issue: https://app.asana.com/0/11127829865276/15184529953373")
def test_foreign_aaa_uc():
    builtins = builtin.builtInSPs()
    ripl = get_ripl()
    ripl.bind_foreign_sp("test_sym_dir_mult", builtins["make_uc_sym_dir_mult"])

    ripl.assume("f", "(test_sym_dir_mult 1 1)")
    assert ripl.sample("f")["counts"] == [0]

    ripl.observe("(f)", "atom<0>")
    assert ripl.sample("f")["counts"] == [1]

    ripl.infer(defaultInfer())
    assert ripl.sample("f")["counts"] == [1]

@skipWhenInParallel("Calling into Lite from Puma is not thread-safe. Issue: https://app.asana.com/0/11127829865276/15184529953373")
@statisticalTest
def test_foreign_aaa_infer():
    "Same as test.inference_quality.micro.test_misc_aaa.testMakeBetaBernoulli1"
    builtins = builtin.builtInSPs()
    ripl = get_ripl()
    ripl.bind_foreign_sp("test_beta_bernoulli", builtins["make_uc_beta_bernoulli"])

    ripl.assume("a", "(normal 10.0 1.0)")
    ripl.assume("f", "(test_beta_bernoulli a a)")
    ripl.predict("(f)", label="pid")

    for _ in range(20): ripl.observe("(f)", "true")

    predictions = collectSamples(ripl,"pid")
    ans = [(False,.25), (True,.75)]
    return reportKnownDiscrete(ans, predictions)

def test_foreign_latents():
    builtins = builtin.builtInSPs()
    ripl = get_ripl()
    ripl.bind_foreign_sp("test_lazy_hmm", builtins["make_lazy_hmm"])

    ripl.assume("f", "(test_lazy_hmm (simplex 1) (id_matrix 1) (id_matrix 1))")
    assert ripl.sample("f")[0] == []

    ripl.observe("(f 1)", "atom<0>")
    assert ripl.sample("f")[0] == [np.matrix([[1]]), np.matrix([[1]])]

    ripl.infer(defaultInfer())
    assert ripl.sample("f")[0] == [np.matrix([[1]]), np.matrix([[1]])]

@skipWhenInParallel("Calling into Lite from Puma is not thread-safe. Issue: https://app.asana.com/0/11127829865276/15184529953373")
@statisticalTest
def test_foreign_latents_infer():
    "Same as test.inference_quality.micro.test_latents.testHMMSP1"

    builtins = builtin.builtInSPs()
    ripl = get_ripl()
    ripl.bind_foreign_sp("test_lazy_hmm", builtins["make_lazy_hmm"])

    ripl.assume("f", """
(test_lazy_hmm
 (simplex 0.5 0.5)
 (matrix (array (array 0.7 0.3)
                (array 0.3 0.7)))
 (matrix (array (array 0.9 0.2)
                (array 0.1 0.8))))
""")
    ripl.observe("(f 1)","atom<0>")
    ripl.observe("(f 2)","atom<0>")
    ripl.observe("(f 3)","atom<1>")
    ripl.observe("(f 4)","atom<0>")
    ripl.observe("(f 5)","atom<0>")
    ripl.predict("(f 6)",label="pid")
    ripl.predict("(f 7)")
    ripl.predict("(f 8)")

    predictions = collectSamples(ripl,"pid")
    ans = [(0,0.6528), (1,0.3472)]
    return reportKnownDiscrete(ans, predictions)

def test_unpicklable_sp_sequential():
    'If we attempt to bind an unpicklable SP in sequential mode, should work'
    ripl = get_ripl()
    ripl.infer('(resample 2)')
    ripl.bind_foreign_sp('f', binaryNum(lambda x, y: 10*x + y))

def test_unpicklable_sp_parallel():
    '''
    If we attempt to bind an unpicklable SP and the engine is in parallel
    or emulating mode, check that we get the proper warning.
    '''
    for mode in ['serializing', 'thread_ser', 'multiprocess']:
        yield check_unpicklable_sp_parallel, mode

def check_unpicklable_sp_parallel(mode):
    ripl = get_ripl()
    resample = '[INFER (resample_{0} 2)]'.format(mode)
    ripl.execute_instruction(resample)
    regexp = 'SP not picklable.'
    with assert_raises_regexp(TypeError, regexp):
        ripl.bind_foreign_sp('f', binaryNum(lambda x, y: 10*x + y))

def test_return_foreign_sp():
    'Foreign SPs can be returned as the result of directives.'
    ripl = get_ripl()
    ripl.bind_foreign_sp('f', binaryNum(lambda x, y: 10*x + y))
    ripl.sample('f')
