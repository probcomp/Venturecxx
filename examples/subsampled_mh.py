import sys
sys.path += ['/usr/lib/python2.7/dist-packages', '/usr/local/lib/python2.7/dist-packages']

import numpy as np
import time
import subsampled_mh_utils
from venture.shortcuts import make_lite_church_prime_ripl
make_ripl = make_lite_church_prime_ripl
v = make_ripl()

D = 3
N = 10
w = np.random.normal(0, np.sqrt(0.1), D + 1).tolist()
X = np.random.normal(0, 1, [N, D])
f = X.dot(w[1:]) + w[0]
y = np.random.random(N) < 1 / (1 + np.exp(-f))
X = X.tolist()
y = y.tolist()

prog = """
[assume D %d]
[assume mu (repeat 0 (+ D 1))]
[assume sigma (repeat (sqrt 0.1) (+ D 1))]
[assume w (scope_include (quote w) 0 (multivariate_diag_normal mu sigma))]
[assume y_x (lambda (x) (bernoulli (linear_logistic w x)))]
""" % D

def loadData(v, X, y, N):
    tic = time.clock()
    for n in xrange(N):
        v.observe('(y_x (vector %s))' \
                  % ' '.join(['%f' % x for x in X[n]]), y[n])
    t_obs = time.clock() - tic
    print "It takes", t_obs, "seconds to load observations."

T = 100
Tthin = 1
Nsamples = (T + Tthin - 1) / Tthin

# Std of the random walk proposal
sig_prop = 0.3

# Austerity
Nbatch = 2
k0 = 3
epsilon = 0.1

# Run MH with Random Walk Proposal
v.clear()
subsampled_mh_utils.loadUtilSPs(v)
v.execute_program(prog);
loadData(v, X, y, len(X))
rst = {'ts': list(), 'ws': list()}

t_start = time.clock()
for i in xrange(Nsamples):
    if i % (Nsamples/10) == 0:
        print i, "/", Nsamples, "time:", time.clock() - t_start

    v.infer('(mh_kernel_update w all true %s false %d)' % (repr(sig_prop), Tthin))

    rst['ts'].append(time.clock() - t_start)
    rst['ws'].append(v.sample('w'))
rst_mh = rst

# Run Subsampled_MH with Random Walk Proposal
v.clear()
subsampled_mh_utils.loadUtilSPs(v)
v.execute_program(prog);
loadData(v, X, y, len(X))
rst = {'ts': list(),
       'ws': list()}

t_start = time.clock()
for i in xrange(Nsamples):
    if i % (Nsamples/10) == 0:
        print i, "/", Nsamples, "time:", time.clock() - t_start

    v.infer('(subsampled_mh w all %d %d %s true %s false %d)' % (Nbatch, k0, repr(epsilon), repr(sig_prop), Tthin))

    rst['ts'].append(time.clock() - t_start)
    rst['ws'].append(v.sample('w'))

rst_submh = rst
