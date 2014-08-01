from venture.test.config import get_ripl, defaultInfer, skipWhenInParallel, collectSamples
from venture.test.stats import statisticalTest, reportKnownDiscrete
from venture.lite import builtin

import numpy as np

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
