from venture.test.config import get_ripl
from venture.lite import builtin

def test_foreign_aaa():
    builtins = builtin.builtInSPs()
    ripl = get_ripl()
    ripl.bind_foreign_sp("test_sym_dir_mult", builtins["make_sym_dir_mult"])

    ripl.assume("f", "(test_sym_dir_mult 1 1)")
    assert ripl.sample("f")["counts"] == [0]

    ripl.observe("(f)", "atom<0>")
    assert ripl.sample("f")["counts"] == [1]

    ripl.infer(10)
    assert ripl.sample("f")["counts"] == [1]

def test_foreign_aaa_resampled():
    builtins = builtin.builtInSPs()
    ripl = get_ripl()
    ripl.bind_foreign_sp("test_sym_dir_mult", builtins["make_sym_dir_mult"])

    ripl.assume("a", "(gamma 1 1)")
    ripl.assume("f", "(test_sym_dir_mult a 1)")
    assert ripl.sample("f")["counts"] == [0]

    ripl.observe("(f)", "atom<0>")
    assert ripl.sample("f")["counts"] == [1]

    ripl.infer(10)
    assert ripl.sample("f")["counts"] == [1]

def test_foreign_aaa_uc():
    builtins = builtin.builtInSPs()
    ripl = get_ripl()
    ripl.bind_foreign_sp("test_sym_dir_mult", builtins["make_uc_sym_dir_mult"])

    ripl.assume("f", "(test_sym_dir_mult 1 1)")
    assert ripl.sample("f")["counts"] == [0]

    ripl.observe("(f)", "atom<0>")
    assert ripl.sample("f")["counts"] == [1]

    ripl.infer(10)
    assert ripl.sample("f")["counts"] == [1]
