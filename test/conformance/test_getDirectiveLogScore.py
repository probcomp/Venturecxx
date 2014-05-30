from venture.test.config import get_ripl
from nose.tools import assert_equal, assert_less
import numpy as np

def testgetDirectiveLogScore():
    ripl = get_ripl()
    
    src = \
    """
        [assume x (scope_include (quote dummy) 0 (normal 0 1))]
        """
    ripl.execute_program(src)
    trace = ripl.sivm.core_sivm.engine.getDistinguishedTrace()
    logscore_lite = trace.getDirectiveLogScore(1)
    val = trace.groundValueAt(trace.scopes['dummy'][0].pop()).number
    logscore_true = -0.5*np.log(2*np.pi) - 0.5*val*val
    
    assert_equal(logscore_lite, logscore_true)
