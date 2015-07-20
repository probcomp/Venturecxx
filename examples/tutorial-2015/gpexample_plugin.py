import sys
sys.path.append('.')

import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as clr
# Let's see what we need here
# from models.covFunctions import *
# from models.tools import array

from venture import shortcuts
import venture.lite.types as t
import venture.lite.sp as sp
from venture.lite.function import VentureFunction
from venture.lite.builtin import deterministic_typed
import gpmem
import pickle
import collections
from numpy.random import random as rand
import scipy.spatial.distance as spdist

@np.vectorize
def regexmpl_f_noiseless(x):
    return 0.3 + 0.4*x + 0.5*np.sin(2.7*x) + (1.1/(1+x**2))


# Covariance functions
def squared_exponential(sf, l):
    def f(x1, x2):
        A = spdist.cdist([[x1/l]],[[x2/l]],'sqeuclidean')
        ans = sf * np.exp(-0.5*A)[0,0]
        return ans
    return f

def whitenoise(s):
    def f(x1, x2):
        tol = 1.e-9  # Tolerance for declaring two vectors "equal"
        M = spdist.cdist([[x1]], [[x2]], 'sqeuclidean')
        A = s * (M < tol)[0,0]
        return A
    return f

def periodic(l,p,sf):
    def f(x1, x2):
        A = np.sqrt(spdist.cdist([[x1]],[[x2]],'sqeuclidean'))[0,0]
        A = np.pi*A/p
        A = np.sin(A)/l
        A = A * A
        A = sf *np.exp(-2.*A)
        return A
    return f

def linear(sf):
    def f(x1, x2):
        return sf * (x1*x2 + 1e-10)  # 1e-10 required for numerical accuracy
    return f

covType = sp.SPType([t.NumberType(), t.NumberType()], t.NumberType())

def __venture_start__(ripl, *args):

    # External SPs
    argmaxSP = deterministic_typed(np.argmax, [t.HomogeneousArrayType(t.NumberType())], t.NumberType())
    absSP = deterministic_typed(abs, [t.NumberType()], t.NumberType())
    make_se_SP = deterministic_typed(lambda sf, l:
                VentureFunction(squared_exponential(sf, l),
                    name="SE", parameter=[sf,l], sp_type=covType),
            [t.NumberType(), t.NumberType()], t.AnyType("VentureFunction"))
    make_whitenoise_SP = deterministic_typed(lambda s:
                VentureFunction(whitenoise(s),
                    name="WN",parameter=[s], sp_type=covType),
            [t.NumberType()], t.AnyType("VentureFunction"))
    make_periodic_cov_SP = deterministic_typed(lambda l, p, sf:
                VentureFunction(periodic(l, p, sf),
                    name="PER",parameter=[l,p,sf], sp_type=covType),
            [t.NumberType(), t.NumberType(), t.NumberType()], t.AnyType("VentureFunction"))
    make_linear_cov_SP = deterministic_typed(lambda sf:
                VentureFunction(linear(sf),
                    name="LIN",parameter=[sf], sp_type=covType),
            [t.NumberType()], t.AnyType("VentureFunction"))
    make_const_func_SP = deterministic_typed(lambda c:
            VentureFunction(lambda x: c,
                sp_type = sp.SPType([], t.NumberType())),
            [t.NumberType()], t.AnyType("VentureFunction"))

    add_funcs_SP = deterministic_typed(lambda f1, f2: VentureFunction(lambda x1,x2: f1(x1,x2) + f2(x1,x2), sp_type=covType),
        [t.AnyType("VentureFunction"), t.AnyType("VentureFunction")],
        t.AnyType("VentureFunction"))
    mult_funcs_SP = deterministic_typed(lambda f1, f2: VentureFunction(lambda x1,x2: f1(x1,x2) * f2(x1,x2), sp_type=covType),
        [t.AnyType("VentureFunction"), t.AnyType("VentureFunction")],
        t.AnyType("VentureFunction"))

    ripl.bind_foreign_sp('gpmem', gpmem.gpmemSP)
    ripl.bind_foreign_inference_sp('argmax_of_array', argmaxSP)
    ripl.bind_foreign_sp('abs', absSP)
    ripl.bind_foreign_sp('make_squaredexp', make_se_SP)
    ripl.bind_foreign_sp('add_funcs', add_funcs_SP)
    ripl.bind_foreign_sp('mult_funcs', mult_funcs_SP)
    ripl.bind_foreign_sp('make_whitenoise', make_whitenoise_SP)
    ripl.bind_foreign_sp('make_periodic_cov', make_periodic_cov_SP)
    ripl.bind_foreign_sp('make_linear_cov', make_linear_cov_SP)
    ripl.bind_foreign_sp('make_const_func', make_const_func_SP)


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

    # Plotting
    def plot_lines(xs, yss, data_xs, data_ys, ymin, ymax, huemin, huemax, linewidth):
        hues = np.linspace(huemin, huemax, len(yss))
        fig, ax = plt.subplots(1)
        for (ys, hue) in zip(yss, hues):
            ax.plot(xs, ys, color=clr.hsv_to_rgb([hue, 1, 1]), linewidth=linewidth)
        ax.scatter(data_xs, data_ys, color='k')
        ax.set_ylim(ymin, ymax)
        plt.show()
        # plt.savefig('plotlines_fig.png')
    plot_lines_sp = deterministic_typed(plot_lines,
            [t.HomogeneousArrayType(t.NumberType()), # xs
                t.HomogeneousArrayType(t.HomogeneousArrayType(t.NumberType())), # yss
                t.HomogeneousArrayType(t.NumberType()), # data_xs
                t.HomogeneousArrayType(t.NumberType()), # data_ys
                t.NumberType(), # ymin
                t.NumberType(), # ymax
                t.NumberType(), # huemin
                t.NumberType(), # huemax
                t.NumberType(), # linewidth
                ],
            t.NilType())
    ripl.bind_foreign_inference_sp('plot_lines', plot_lines_sp)
