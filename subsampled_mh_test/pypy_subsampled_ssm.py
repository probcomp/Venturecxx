## Subsampled MH for Joint DP Mixture of Logistic Regression Experts

import sys
sys.path += ['/usr/lib/python2.7/dist-packages', '/usr/local/lib/python2.7/dist-packages']

import random
import numpy as np
import time
from pypy_io_utils import loadSSMData, saveObj
from venture.shortcuts import make_lite_church_prime_ripl
make_ripl = make_lite_church_prime_ripl

def main(data_source_, epsilon_, N_):
  ##########################################
  #### Parameters

  print "data_source:", data_source_
  print "epsilon:", epsilon_
  print "N_:", N_

  rand_seed = 101
  random.seed(rand_seed)
  np.random.seed(rand_seed)

  ## Data
  data_source = data_source_ # "ssm"

  ## Load data
  if data_source == "ssm3":
    ##### SSM Data
    data_file = 'data/input/ssm3.json'
    N, X, sig_noise = loadSSMData(data_file)
    print "N:", N, "sig_noise:", sig_noise
  elif data_source == "ssm4":
    ##### SSM Data
    data_file = 'data/input/ssm4.json'
    N, X, sig_noise = loadSSMData(data_file)
    print "N:", N, "sig_noise:", sig_noise
  else:
    assert False

  if N_ != 0:
    N = min(N, N_)
    print "N:", N
  tag_N = "N%d" % N

  ## Model
  # Hyper-param for sig
  # sig = gamma(al_sig, bt_sig)
  al_sig = 1;
  bt_sig = 10;

  #sig_noise = 0.05;

  b = 1.1;

  # Prior for a is Unim[0,1]
  #a = rand;

  ## Sampler
  time_max = 1e5
  T = 100000
  Tthin = 1
  Nsamples = (T + Tthin - 1) / Tthin

  P = 10
  pLen = 10
  step_h = 1
  step_a = 1

  Th = 20

  Tsave = 10

  # Austerity
  Nbatch = 100
  k0 = 3
  epsilon = epsilon_

  use_austerity = epsilon != 0 # False # True
  tag_austerity = "submh_%.3f" % epsilon if use_austerity else "mh"

  # jointdplr_mnist_mh or jointdplr_mnist_submh
  tag = "_".join(["pypy_ssm_init", data_source, tag_N, tag_austerity])

  stage_file = 'data/output/ssm/stage_'+tag
  print "stage_file:", stage_file

  ##########################################
  #### Initialization
  prog = """
  [clear]
  [assume a (scope_include (quote a) 0 (uniform_continuous 0 1))]
  [assume sig (scope_include (quote sig) 0 (gamma {al_sig} {bt_sig}))]
  [assume a_i (mem (lambda (i) a))]
  [assume h (mem (lambda (i) (scope_include (quote h) i (
        if (<= i 0) 0
            (normal (min (/ (+ (h (- i 1)) 1.0) (+ (a_i i) 1.0))
                         (/ (- (h (- i 1)) {b}) (- (a_i i) {b})))
                    sig)))))]
  [assume x (lambda (i) (normal (pow (h i) 2) {sig_noise}))]
  """.format(b = b, al_sig = al_sig, bt_sig = bt_sig, sig_noise = sig_noise)
  v = make_ripl()
  #v.set_seed(rand_seed)
  v.execute_program(prog);

  ## Load observations.
  tic = time.clock()
  for n in xrange(N):
    if (n + 1) % round(N / 10) == 0:
      print "Processing %d/%d observations." % (n + 1, N)
    v.observe('(x %d)' % n, X[n])

    if (n + 1) % 10 == 0:
      start = max(1, n - 9)
      end = n
      if not use_austerity:
        infer_str = '(pgibbs h (ordered_range {start} {end}) {P} 1)'.format(start = start, end = end, P = P)
      else:
        infer_str = '(pgibbs_update h (ordered_range {start} {end}) {P} 1)'.format(start = start, end = end, P = P)
      v.infer(infer_str)

  t_obs = time.clock() - tic
  print "It takes", t_obs, "seconds to load observations."

  trace = v.sivm.core_sivm.engine.getDistinguishedTrace()

  rst = {'ts': list(),
         'ts_sampa': list(),
         'ts_samph': list(),
         'a': list(),
         'sig': list(),
         'iters_h': list(),
         'ts_h': list(),
         'h': list()}

  ##########################################
  #### Run and Record

  v.infer('(mh a all 1)') # First iteration to run engine.incorporate whose running time is excluded from record.


  # Run one sweep
  #print "Running the first sweep"
  #start = 1
  #tic = time.clock()
  #while True:
  #  if (start - 1) % round(N / 10) == 0:
  #    print "Sampling %d/%d h's." % (start, N)

  #  end = min(N-1, start + pLen - 1)
  #  if not use_austerity:
  #    #infer_str = '(pgibbs h ordered {P} 1)'.format(P = P)
  #    infer_str = '(pgibbs h (ordered_range {start} {end}) {P} {step_h})'.format(start = start, end = end, P = P, step_h = step_h)
  #  else:
  #    #infer_str = '(pgibbs h ordered {P} 1 true true)'.format(P = P)
  #    infer_str = '(pgibbs h (ordered_range {start} {end}) {P} {step_h} true true)'.format(start = start, end = end, P = P, step_h = step_h)
  #  v.infer(infer_str)
  #  start += pLen
  #  if start >= N:
  #    break
  #t_firstsweep = time.clock() - tic
  #print "It takes", t_obs, "seconds to run the first sweep."

  t_start = time.clock()
  t_h_cum = 0
  i_save = -1
  t_a = 0.0
  t_h = 0.0
  t_sampa = 0.0
  t_samph = 0.0
  avg_t_a = 0.0
  avg_t_h = 0.0
  start = 1

  for i in xrange(Nsamples):
    # Run inference.

    if t_h == 0:
      t_h = 1
      t_a = 1
    else:
      avg_t_h = t_h / float(step_h)
      avg_t_a = t_a / float(step_a)
      if avg_t_h > avg_t_a:
        step_h = 1
        step_a = max(1, round(avg_t_h / avg_t_a))
      else:
        step_a = 1
        step_h = max(1, round(avg_t_a / avg_t_h))
    print "avg_t_a:", avg_t_a, "avg_t_h:", avg_t_h, "t_a:", t_a, "t_h:", t_h, "step_a:", step_a, "step_h:", step_h

    # PGibbs for h
    #start = np.random.randint(N - pLen + 1)
    step_h = int(step_h)
    step_a = int(step_a)
    t_sample_start = time.clock()
    for _ in range(step_h):
      end = min(N-1, start + pLen - 1)
      if not use_austerity:
        #infer_str = '(pgibbs h ordered {P} 1)'.format(P = P)
        infer_str = '(pgibbs h (ordered_range {start} {end}) {P} 1)'.format(start = start, end = end, P = P)
      else:
        #infer_str = '(pgibbs h ordered {P} 1 true true)'.format(P = P)
        infer_str = '(pgibbs_update h (ordered_range {start} {end}) {P} 1)'.format(start = start, end = end, P = P)
      start += pLen
      if start >= N:
        start = 1

      v.infer(infer_str)
    t_h = time.clock() - t_sample_start
    t_samph += t_h

    # Global variables.
    if not use_austerity:
      infer_str = '(cycle ((mh a 0 1) (mh sig 0 1)) {step_a})'.format(step_a = step_a)
    else:
      infer_str = ('(cycle ( ' + \
                   '(subsampled_mh a   0 {Nbatch} {k0} {epsilon} false 0 false 1) ' + \
                   '(subsampled_mh sig 0 {Nbatch} {k0} {epsilon} false 0 false 1)) {step_a})').format(
                    Nbatch = Nbatch, k0 = k0, epsilon = epsilon, step_a = step_a)
    t_sample_start = time.clock()
    v.infer(infer_str)
    t_a = time.clock() - t_sample_start
    t_sampa += t_a

    # Record.
    rst['ts'].append(time.clock() - t_start - t_h_cum)
    rst['ts_sampa'].append(t_sampa)
    rst['ts_samph'].append(t_samph)
    rst['a'].append(next(iter(trace.scopes['a'][0])).value.number)
    rst['sig'].append(next(iter(trace.scopes['sig'][0])).value.number)
    print "a:", rst['a'][-1], "sig:", rst['sig'][-1]

    # Record h.
    if (i + 1) % Th == 0:
      print "Storing h..."
      tic = time.clock()

      rst['h'].append([next(iter(trace.scopes['h'][i])).value.number for i in xrange(N)])

      t_h_cum += time.clock() - tic
      rst['iters_h'].append(i)
      rst['ts_h'].append(t_h_cum)

    # Save temporary results.
    if (i + 1) % Tsave == 0:
      saveObj(rst, stage_file)
      i_save = i

    time_run = time.clock() - t_start
    print i, "/", Nsamples, "time:", time_run
    if time_run > time_max:
      break

  # If savemat is not called at the last iteration, call it now.
  if i_save != i:
    saveObj(rst, stage_file)

if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument('--data', dest='data_source_', default='ssm3', help='data file')
  parser.add_argument('--eps',dest='epsilon_', default=0.0, type=float, help='Epsilon')
  parser.add_argument('--N',dest='N_', default=0, type=int, help='N')
  args = vars(parser.parse_args())
  main(**args)

