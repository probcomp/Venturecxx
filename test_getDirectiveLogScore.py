# test case for Trace.getDirectiveLogScore(directive_id) method

from venture.shortcuts import *
import numpy as np
v = make_lite_church_prime_ripl()
src = \
"""
[assume x (scope_include (quote dummy) 0 (normal 0 1))]
"""
v.execute_program(src)
trace = v.sivm.core_sivm.engine.getDistinguishedTrace()
logscore_lite = trace.getDirectiveLogScore(1)
val = trace.groundValueAt(trace.scopes['dummy'][0].pop()).number
logscore_true = -0.5*np.log(2*np.pi) - 0.5*val*val
print logscore_lite == logscore_true
