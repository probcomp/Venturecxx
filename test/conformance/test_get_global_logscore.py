import warnings
from nose import SkipTest
from nose.tools import assert_almost_equal, eq_
import numpy as np
from scipy import stats

from venture.test.config import get_ripl, on_inf_prim, broken_in
from venture.lite.psp import LikelihoodFreePSP
from venture.lite import value as v
from venture.lite.builtin import typed_nr
from venture.lite.exception import LogScoreWarning

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
@broken_in("puma", "TODO: fix getGlobalLogScore in PUMA. Issue: https://app.asana.com/0/12610813584901/23899154336705")
def test_logscore_likelihood_free():
    "Should warn user that there are likelihood-free SP's"
    ripl = setup_likelihood_free()
    for _ in range(100):
        ripl.observe('(flip)', 'true')
    ripl.infer('(incorporate)')
    ripl.predict('(test1 0)')
    ripl.predict('(test2 0)')
    # make sure the user is warned when attempting to retrieve global logscore
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        logscore = ripl.get_global_logscore()
        # Verify some things
        assert len(w) == 1
        w = w[0]
        assert w.category is LogScoreWarning
        eq_(w.message.message,
            "There are 2 likelihood-free SP's in the trace. These are not included in the logscore.")
    logscore_true = -100*np.log(2)
    assert_almost_equal(logscore, logscore_true)

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
