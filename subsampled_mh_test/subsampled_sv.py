## Subsampled MH for Joint DP Mixture of Logistic Regression Experts

import numpy as np
import scipy.io
import time
import shelve
from venture.shortcuts import make_lite_church_prime_ripl
make_ripl = make_lite_church_prime_ripl

def main(data_source_, epsilon_):
  ##########################################
  #### Parameters

  print "data_source:", data_source_
  print "epsilon:", epsilon_

  ## Data
  data_source = data_source_ # "sv"

  ## Load data
  if data_source == "sv":
    ##### SV Data
    from load_data import loadSVData
    data_file = 'data/input/sv.mat'
    N, X = loadSVData(data_file)
    print "N:", N
  else:
    assert False


  ## Model
  # Hyper-param for mu
  std_mu = 0.1;

  # Hyper-param for phi
  a_phi = 100;
  b_phi = 1;

  # Hyper-param for sig
  al_sig = 1;
  bt_sig = 100;


  ## Sampler
  time_max = 1e5
  T = 100000
  Tthin = 1
  Nsamples = (T + Tthin - 1) / Tthin

  P = 3
  Tglobal = P

  Th = 100

  Tsave = 100

  # Austerity
  Nbatch = 50
  k0 = 3
  epsilon = epsilon_

  use_austerity = epsilon != 0 # False # True
  tag_austerity = "submh_%.2f" % epsilon if use_austerity else "mh"

  # jointdplr_mnist_mh or jointdplr_mnist_submh
  tag = "_".join(["sv_test", data_source, tag_austerity])

  stage_file = 'data/output/sv/stage_'+tag
  result_file = 'data/output/sv/result_'+tag

  ##########################################
  #### Initialization
  prog = """
  [clear]
  [assume mu (scope_include (quote mu) 0 (normal 0 {std_mu}))]
  [assume phi (scope_include (quote phi) 0 (beta {a_phi} {b_phi}))]
  [assume sig (scope_include (quote sig) 0 (gamma {al_sig} {bt_sig}))]
  [assume mu_i (mem (lambda (i) mu))]
  [assume h (mem (lambda (i) (scope_include (quote h) i (
      if (<= i 0)
          (normal (mu_i i) sig)
          (normal (+ (mu_i i)
                     (* phi
                        (- (h (- i 1))
                           (mu_i i))))
                  sig)))))]
  [assume x (lambda (i) (normal 0 (exp (/ (h i) 2))))]
  """.format(std_mu = std_mu, a_phi = a_phi, b_phi = b_phi, al_sig = al_sig, bt_sig = bt_sig)
  v = make_ripl()
  v.execute_program(prog);

  ## Load observations.
  tic = time.clock()
  for n in xrange(N):
    if (n + 1) % round(N / 10) == 0:
      print "Processing %d/%d observations." % (n + 1, N)
    v.observe('(x %d)' % n, X[n])
  t_obs = time.clock() - tic
  print "It takes", t_obs, "seconds to load observations."

  trace = v.sivm.core_sivm.engine.getDistinguishedTrace()

  rst = {'ts': list(),
         'mu': list(),
         'phi': list(),
         'sig': list(),
         'iters_h': list(),
         'ts_h': list(),
         'h': list()}

  ##########################################
  #### Run and Record

  v.infer('(mh mu all 1)') # First iteration to run engine.incorporate whose running time is excluded from record.

  t_start = time.clock()
  t_h_cum = 0
  i_save = -1
  for i in xrange(Nsamples):
    # Run inference.
    if not use_austerity:
      # PGibbs for h
      infer_str = '(pgibbs h all 1 {P})'.format(P = P)
      v.infer(infer_str)

      # Global variables.
      infer_str = '(cycle ((mh mu 0 1) (mh phi 0 1) (mh sig 0 1)) {Tglobal})'.format(Tglobal = Tglobal)
      v.infer(infer_str)
    else:
      # PGibbs for h
      infer_str = '(pgibbs h all 1 {P} true true)'.format(P = P)
      v.infer(infer_str)

      # Global variables.
      infer_str = ('(cycle ( ' + \
                   '(subsampled_mh mu  0 1 {Nbatch} {k0} {epsilon}) ' + \
                   '(subsampled_mh phi 0 1 {Nbatch} {k0} {epsilon}) ' + \
                   '(subsampled_mh sig 0 1 {Nbatch} {k0} {epsilon})) {Tglobal})').format(
                    Nbatch = Nbatch, k0 = k0, epsilon = epsilon, Tglobal = Tglobal)
      v.infer(infer_str)

    # Record.
    rst['ts'].append(time.clock() - t_start - t_h_cum)
    rst['mu'].append(next(iter(trace.scopes['mu'][0])).value.number)
    rst['phi'].append(next(iter(trace.scopes['phi'][0])).value.number)
    rst['sig'].append(next(iter(trace.scopes['sig'][0])).value.number)

    # Record h.
    if (i + 1) % Th == 0:
      print "Storing h..."
      tic = time.clock()

      rst['iters_h'].append(i)
      rst['ts_h'].append(t_h_cum)
      rst['hs'].append([next(iter(trace.scopes['h'][i])) for i in xrange(N)])

      t_h_cum += time.clock() - tic

    # Save temporary results.
    if (i + 1) % Tsave == 0:
      scipy.io.savemat(stage_file, rst)
      i_save = i

    time_run = time.clock() - t_start
    print i, "/", Nsamples, "time:", time_run
    if time_run > time_max:
      break

  # If savemat is not called at the last iteration, call it now.
  if i_save != i:
    scipy.io.savemat(stage_file, rst)

  ##########################################
  #### Save workspace
  from cPickle import PicklingError
  my_shelf = shelve.open(result_file,'n') # 'n' for new
  for key in dir():
    try:
      my_shelf[key] = locals()[key]
    except (TypeError, PicklingError):
      #
      # __builtins__, my_shelf, and imported modules can not be shelved.
      #
      print('Not shelved: {0}'.format(key))
  my_shelf.close()

if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument('--data', dest='data_source_', default='sv', help='data file')
  parser.add_argument('--eps',dest='epsilon_', default=0.0, type=float, help='Epsilon')
  args = vars(parser.parse_args())
  main(**args)

