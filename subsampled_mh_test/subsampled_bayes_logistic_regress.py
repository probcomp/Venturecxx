## Subsampled MH for Bayesian Logistic Regression

import numpy as np
import scipy.io
import time
import shelve
from venture.shortcuts import make_lite_church_prime_ripl
make_ripl = make_lite_church_prime_ripl

##########################################
#### Parameters

# Data
data_source = "mnist" # "mnist" # "synthetic"

# Parameters for sampling
T = 10000
Tthin = 1
Nsamples = (T + Tthin - 1) / Tthin

Tsave = 100

# Proposal
sig_prop = 0.01

# Austerity
Nbatch = 600
k0 = 3
epsilon = 0.01

use_austerity = True
tag_austerity = "submh" if use_austerity else "mh"

# bayeslr_mnist_mh or bayeslr_mnist_submh
tag = "_".join(["bayeslr", data_source, tag_austerity])

stage_file = 'data/output/bayeslr/stage_'+tag
result_file = 'data/output/bayeslr/result_'+tag

##########################################
#### Initialization
v = make_ripl()

if data_source == "synthetic":

  ##### Synthetic Data
  D = 2
  N = 100
  w = np.random.normal(0, np.sqrt(0.1), D + 1).tolist()
  X = np.random.normal(0, 1, [N, D])
  f = X.dot(w[1:]) + w[0]
  y = np.random.random(N) < 1 / (1 + np.exp(-f))
  X = X.tolist()
  y = y.tolist()

elif data_source == "mnist":

  ##### Load MNIST Data
  from load_data import loadData
  data_file = 'data/input/mnist_D50_7_9.mat'
  N, D, X, y = loadData(data_file)
  print "N:", N, "D:", D

prog = """
[clear]
[assume D %d]
[assume mu (zeros_array (+ D 1))]
[assume Sigma (diagonal_matrix (scalar_product (sqrt 0.1) (ones_array (+ D 1))))]
[assume w (scope_include (quote w) 0 (multivariate_normal mu Sigma))]
[assume y_x (lambda (x) (bernoulli (linear_logistic w x)))]
""" % D
v.execute_program(prog);

# Load observations.
tic = time.clock()
for n in xrange(N):
  if (n + 1) % round(N / 10) == 0:
    print "Processing %d/%d observations." % (n + 1, N)
  v.observe('(scope_include (quote y) %d (y_x (array %s)))' \
            % (n, ' '.join(['%f' % x for x in X[n]])), y[n])
t_obs = time.clock() - tic
print "It takes", t_obs, "seconds to load observations."

rst = {'ts': list(),
       'ws': list()}

##########################################
#### Run and Record

t_start = time.clock()
for i in xrange(Nsamples):
  print i, "/", Nsamples, "time:", time.clock() - t_start

  if not use_austerity:
    v.infer('(mh w all %d true %s)' % (Tthin, repr(sig_prop)))
  else:
    v.infer('(subsampled_mh w all %d %d %d %s true %s)' % (Tthin, Nbatch, k0, repr(epsilon), repr(sig_prop)))

  rst['ts'].append(time.clock() - t_start)
  rst['ws'].append(v.sample('w'))
  if (i + 1) % Tsave == 0:
    scipy.io.savemat(stage_file, rst)

#plot(rst['ts'], [w[0] for w in rst['ws']], 'x-')

# Save workspace
my_shelf = shelve.open(result_file,'n') # 'n' for new
for key in dir():
  if key == 'my_shelf' or key == 'v':
    continue
  try:
    my_shelf[key] = globals()[key]
  except TypeError:
    #
    # __builtins__, my_shelf, and imported modules can not be shelved.
    #
    print('Not shelved: {0}'.format(key))
my_shelf.close()

