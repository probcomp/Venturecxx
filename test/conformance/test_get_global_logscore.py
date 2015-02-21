import warnings
from nose import SkipTest
from nose.tools import assert_almost_equal, eq_
import numpy as np
from scipy import stats

from venture.test.config import get_ripl, on_inf_prim, broken_in
from venture.lite.psp import LikelihoodFreePSP
from venture.lite import value as v
from venture.lite.builtin import typed_nr

@on_inf_prim("none")
def test_global_logscore():
    ripl = get_ripl()
    for _ in range(100):
        ripl.observe('(flip)', 'true')
    ripl.infer('(incorporate)')
    logscore = ripl.get_global_logscore()
    logscore_true = -100*np.log(2)
    assert_almost_equal(logscore, logscore_true)

@on_inf_prim("none")
def test_global_logscore_coupled():
    raise SkipTest("Exchangeable coupling breaks get_global_logscore. Issue: https://app.asana.com/0/11127829865276/14115439427385")
    ripl = get_ripl()
    ripl.assume('f', '(make_beta_bernoulli 1.0 1.0)')
    for _ in range(100):
        ripl.observe('(f)', 'true')
    ripl.infer('(incorporate)')
    logscore = ripl.get_global_logscore()
    logscore_true = -np.log(100)
    assert_almost_equal(logscore, logscore_true)

@on_inf_prim("none")
def test_logscore_likelihood_free():
    "Shouldn't break in the presence of likelihood-free SP's"
    ripl = setup_likelihood_free()
    for _ in range(100):
        ripl.observe('(flip)', 'true')
    ripl.infer('(incorporate)')
    ripl.predict('(test1 0)')
    ripl.predict('(test2 0)')
    logscore = ripl.get_global_logscore()

def setup_likelihood_free():
    class TestPSP1(LikelihoodFreePSP):
        def simulate(self, args):
            x = args.operandValues[0]
            return x + stats.distributions.norm.rvs()
    tester1 = typed_nr(TestPSP1(), [v.NumberType()], v.NumberType())

    class TestPSP2(LikelihoodFreePSP):
        def simulate(self, args):
            x = args.operandValues[0]
            return x + stats.distributions.bernoulli(0.5).rvs()
    tester2 = typed_nr(TestPSP2(), [v.NumberType()], v.NumberType())
    ripl = get_ripl()
    ripl.bind_foreign_sp('test1', tester1)
    ripl.bind_foreign_sp('test2', tester2)
    return ripl
