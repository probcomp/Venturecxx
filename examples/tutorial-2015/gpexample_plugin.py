import sys
sys.path.append('.')

import numpy as np
from numpy.random import random as rand

import venture.lite.types as t
import venture.lite.sp as sp
from venture.lite.sp_help import deterministic_typed
import regress_mem


@np.vectorize
def regexmpl_f_noiseless(x):
    return 0.3 + 0.4*x + 0.5*np.sin(2.7*x) + (1.1/(1+x**2))


def __venture_start__(ripl, *args):

    # External SPs
    argmaxSP = deterministic_typed(np.argmax, [t.HomogeneousArrayType(t.NumberType())], t.NumberType())
    absSP = deterministic_typed(abs, [t.NumberType()], t.NumberType())

    ripl.bind_foreign_sp('regress_mem', regress_mem.regress_mem)
    ripl.assume('gpmem', 'proc (f, mean, cov) { regress_mem(f, make_gp, mean, cov) }')
    ripl.bind_foreign_inference_sp('argmax_of_array', argmaxSP)
    ripl.bind_foreign_sp('abs', absSP)

    # Gpmem example
    def make_audited_expensive_function(name):
        def expensive_f(x):
            expensive_f.count += 1 # A tracker for how many times I am called
            ans = (0.2 + np.exp(-0.1*abs(x-2))) * np.cos(0.4*x)
            print "[PROBE %s] Probe #%d: %s(%f) = %f" % (expensive_f.name, expensive_f.count, expensive_f.name, x, ans)
            return ans
        expensive_f.count = 0
        expensive_f.name = name
        audited_sp = deterministic_typed(expensive_f, [t.NumberType()], t.NumberType())
        return sp.VentureSPRecord(audited_sp)

    ripl.bind_foreign_sp('make_audited_expensive_function', deterministic_typed(
        make_audited_expensive_function, [t.StringType()], sp.SPType([t.NumberType()], t.NumberType())))

    # Regression example
    @np.vectorize
    def f_noisy(x):
        p_outlier = 0.1
        stdev = (1.0 if rand() < p_outlier else 0.1)
        return np.random.normal(regexmpl_f_noiseless(x), stdev)

    # Generate and save a data set
    # print "Generating regression example data set"
    n = 100
    regexempl_data_xs = np.random.normal(0,1,n)
    regexempl_data_ys = f_noisy(regexempl_data_xs)

    ## The probe function
    def f_restr(x):
        matches = np.argwhere(np.abs(regexempl_data_xs - x) < 1e-6)
        if matches.size == 0:
            raise Exception('Illegal query')
        else:
            assert matches.size == 1
            i = matches[0,0]
            return regexempl_data_ys[i]
    f_restr_sp = deterministic_typed(f_restr, [t.NumberType()], t.NumberType())
    ripl.bind_foreign_sp('get_regexmpl_lookuper', deterministic_typed(
        lambda: sp.VentureSPRecord(f_restr_sp), [], sp.SPType([t.NumberType()], t.NumberType())))

    get_regexempl_data_xs_SP = deterministic_typed(lambda: regexempl_data_xs, [], t.HomogeneousArrayType(t.NumberType()))
    ripl.bind_foreign_sp('get_regexempl_data_xs', get_regexempl_data_xs_SP)
