from nose import SkipTest
from nose.tools import assert_almost_equal
import numpy as np

from venture.test.config import get_ripl, on_inf_prim

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
