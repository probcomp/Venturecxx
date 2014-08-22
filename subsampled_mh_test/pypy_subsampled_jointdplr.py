## Subsampled MH for Joint DP Mixture of Logistic Regression Experts

import sys
sys.path += ['/usr/lib/python2.7/dist-packages', '/usr/local/lib/python2.7/dist-packages']

import random
import numpy as np
import time
from pypy_io_utils import loadData, saveObj
from venture.shortcuts import make_lite_church_prime_ripl
make_ripl = make_lite_church_prime_ripl

def main(data_source_, epsilon_, N_):
  ##########################################
  #### Parameters

  print "data_source:", data_source_
  print "epsilon:", epsilon_
  print "N_:", N_

  rand_seed = 101

  ## Data
  data_source = data_source_ # "mnist" # "mnist_mini" # "synthetic" # "circle"

  ## Load data
  if data_source == "synthetic":
    ##### Synthetic Data
    D = 2
    N = 10
    Ntst = 10

    w = np.random.normal(0, np.sqrt(0.1), D + 1).tolist()
    X = np.random.normal(0, 1, [N, D])
    f = X.dot(w[1:]) + w[0]
    y = np.random.random(N) < 1 / (1 + np.exp(-f))
    X = X.tolist()
    y = y.tolist()

    wtst = np.random.normal(0, np.sqrt(0.1), D + 1).tolist()
    Xtst = np.random.normal(0, 1, [Ntst, D])
    ftst = Xtst.dot(wtst[1:]) + wtst[0]
    ytst = np.random.random(Ntst) < 1 / (1 + np.exp(-ftst))
    Xtst = Xtst.tolist()
    ytst = ytst.tolist()

    print "N:", N, "Ntst:", Ntst, "D:", D
  elif data_source == "mnist":
    ##### MNIST Data
    data_file = 'data/input/mnist_D50_7_9.json'
    N, D, X, y, Ntst, Xtst, ytst = loadData(data_file)
    print "N:", N, "Ntst:", Ntst, "D:", D
  elif data_source == "circle":
    ##### Synthetic Circle Data
    data_file = 'data/input/circle_data.json'
    N, D, X, y, Ntst, Xtst, ytst = loadData(data_file)
    print "N:", N, "Ntst:", Ntst, "D:", D
  elif data_source == "four_cluster":
    data_file = 'data/input/four_cluster_data2.json'
    N, D, X, y, Ntst, Xtst, ytst = loadData(data_file)
    print "N:", N, "Ntst:", Ntst, "D:", D
  else:
    assert False

  if N_ != 0:
    N = min(N, N_)
    print "N:", N
  tag_N = "N%d" % N

  ytst = np.array(ytst)

  ## Model
  # Hyper-param for w
  Sigma_w = 1.0
  # Hyper-param for the conjugate prior of mu_x
  m0 = np.zeros(D) # \mu_0 # Not used in venture
  k0 = 5 # m
  # Hyper-param for the conjugate prior of Sigma_x
  v0 = D + 5 # n_0, must be larger than D
  S0 = np.eye(D) * v0 # Psi # Not used in venture
  # Hyper-param for the Gamma prior of the CRP concentration
  a_alpha = 1
  b_alpha = 1

  ## Sampler
  time_max = 1e5
  T = 100000
  Tthin = 1
  Nsamples = (T + Tthin - 1) / Tthin

  Tzs = 100

  Tpred = 100

  Tsave = 100

  # Proposal
  sig_prop = 0.2
  print "sig_prop:", sig_prop

  # Austerity
  Nbatch = 10
  print "Nbatch:", Nbatch
  k0 = 3
  epsilon = epsilon_

  use_austerity = epsilon != 0 # False # True
  tag_austerity = "submh_%.2f" % epsilon if use_austerity else "mh"

  # Number of MH and Gibbs steps for w and z respectively every iteration
  step_w = 1
  if use_austerity:
    step_z = round(N / 100)
  else:
    step_z = round(N / 100)
  step_z = max(1, step_z)

  # jointdplr_mnist_mh or jointdplr_mnist_submh
  tag = "_".join(["pypy_jointdplr_test", data_source, tag_N, tag_austerity])

  stage_file = 'data/output/jointdplr/stage_'+tag

  ##########################################
  #### Initialization
  prog = """
  [clear]
  [assume D {D}]
  [assume mu_w (zeros_array (+ D 1))]
  [assume Sigma_w (scalar_product {Sigma_w!r} (ones_array (+ D 1)))]
  [assume m0 (zeros_array D)]
  [assume k0 {k0}]
  [assume v0 {v0}]
  [assume S0 (diagonal_matrix (scalar_product v0 (ones_array D)))]
  [assume alpha (scope_include (quote alpha) 0 (gamma {a_alpha!r} {b_alpha!r}))]
  [assume crp (make_crp alpha)]
  [assume z (mem (lambda (i) (scope_include (quote z) i (crp))))]
  [assume w (mem (lambda (z) (scope_include (quote w) z (multivariate_diag_normal mu_w Sigma_w))))]
  [assume cmvn (mem (lambda (z) (make_cmvn m0 k0 v0 S0)))]
  [assume x (lambda (i) ((cmvn (z i))))]
  [assume y (lambda (i x) (bernoulli (linear_logistic (w (z i)) x)))]
  """.format(D = D, Sigma_w = Sigma_w, k0 = k0, v0 = v0, a_alpha = a_alpha, b_alpha = b_alpha)
  v = make_ripl()
  #v.set_seed(rand_seed)
  random.seed(rand_seed)
  np.random.seed(rand_seed)
  v.execute_program(prog);

  ##########################################
  #### Load observations.
  ## Load X and sample.
  tic = time.clock()
  while True:
    v.infer('(mh alpha all 1)')
    if v.sample('alpha') > 4:
        break
  for n in xrange(N):
    if (n + 1) % round(N / 10) == 0:
      print "Processing %d/%d observations." % (n + 1, N)

    v.observe('(x %d)' % n, \
              {'type': 'list', 'value': [{'type': 'real', 'value': x} for x in X[n]]})
    v.infer('(gibbs z %d 1)' %n)

    if (n + 1) % 100 == 0:
      v.infer('(pgibbs z one 3 100)')
      #for _ in range(10):
        #v.infer('(pgibbs z one 3 100)')
        #v.infer('(gibbs z one 100)')
        #v.infer('(mh alpha all 1)')

  t_obs = time.clock() - tic
  print "It takes", t_obs, "seconds to load X."

  ## Load Y.
  tic = time.clock()
  for n in xrange(N):
    if (n + 1) % round(N / 10) == 0:
      print "Processing %d/%d observations." % (n + 1, N)
    v.observe('(y %d (array %s))' % (n, ' '.join(repr(x) for x in X[n])), y[n])
  t_obs = time.clock() - tic
  print "It takes", t_obs, "seconds to load observations."

  ## Load together
  #tic = time.clock()
  #for n in xrange(N):
  #  if (n + 1) % round(N / 10) == 0:
  #    print "Processing %d/%d observations." % (n + 1, N)
  #  v.observe('(x %d)' % n, \
  #            {'type': 'list', \
  #             'value': [{'type': 'real', 'value': x} for x in X[n]]})
  #  v.observe('(y %d (array %s))' % (n, ' '.join(repr(x) for x in X[n])), y[n])
  #t_obs = time.clock() - tic
  #print "It takes", t_obs, "seconds to load observations."

  ## Find CRP and CMVN node
  trace = v.sivm.core_sivm.engine.getDistinguishedTrace()
  crpNode = trace.globalEnv.findSymbol('crp')
  #wNode = trace.globalEnv.findSymbol('w')
  tableCounts = trace.madeSPAuxAt(crpNode).tableCounts
  tables = tableCounts.keys()

  cmvnNode = trace.globalEnv.findSymbol('cmvn')

  rst = {'ts': list(),
         'alphas': list(),
         'zCounts': list(),
         'ws': list(),
         'cmvnN': list(),
         'cmvnXTotal': list(),
         'cmvnSTotal': list(),
         'ts_zs': list(),
         'zs': list(),
         'iters_pred': list(),
         'ts_pred': list(),
         'zs_pred': list(),
         'ys_pred': list(),
         'acc': list()}

  ##########################################
  #### Run and Record

  v.infer('(mh alpha all 1)') # First iteration to run engine.incorporate whose running time is excluded from record.

  t_start = time.clock()
  t_pred_cum = 0
  i_save = -1
  t_w = 0.0
  t_z = 0.0
  for i in xrange(Nsamples):
    # Run inference.

    # Sample w.
    #step_w = max(1, round(float(t_z) / t_w)) if t_w > 0 else 1
    step_w = 1
    print "t_w:", t_w, "t_z:", t_z, "Step_z:", step_z
    if not use_austerity:
      infer_str = '(cycle (' + \
          ' '.join(['(mh_kernel_update w {z} true {sig_prop} false 1)'.format(\
              z = z, sig_prop = sig_prop) for z in tables]) + ' ' + \
          ') {step_w})'.format(step_w = step_w)
    else:
      infer_str = '(cycle (' + ' '.join([\
          '(subsampled_mh w {z} {Nbatch} {k0} {epsilon} true {sig_prop} true 1)'.format(\
              z = z, Nbatch = Nbatch, k0 = k0, epsilon = epsilon, \
              sig_prop = sig_prop) for z in tables]) + ' ' + \
          ') {Tthin})'.format(Tthin = Tthin)
    t_sample_start = time.clock()
    v.infer(infer_str)
    t_w = time.clock() - t_sample_start

    # Sample z and alpha
    step_z = max(1, round(float(t_w) / t_z * step_z)) if t_z > 0 else 1
    if not use_austerity:
      infer_str = '(cycle (' + \
                  '(gibbs z one {step_z}) (mh alpha all 1)) {Tthin})'.format(\
                      step_z = step_z, Tthin = Tthin)
    else:
      infer_str = '(cycle (' + \
                  '(gibbs_update z one {step_z}) (mh_kernel_update alpha all false 0 true 1)) {Tthin})'.format(\
                      step_z = step_z, Tthin = Tthin)
    t_sample_start = time.clock()
    v.infer(infer_str)
    t_z = time.clock() - t_sample_start

    # Find z partition.
    tableCounts = trace.madeSPAuxAt(crpNode).tableCounts
    tables = tableCounts.keys()

    # Record.
    rst['ts'].append(time.clock() - t_start - t_pred_cum)
    rst['alphas'].append(v.sample('alpha'))
    zCountsTable = [[z, count] for z,count in sorted(tableCounts.iteritems())]
    rst['zCounts'].append(zCountsTable)

    ws = list()
    for z in zCountsTable:
      va = next(iter(trace.scopes['w'][z[0]])).value
      ws.append(np.array([vn.number for vn in va.array]))
    rst['ws'].append(ws)

    # Save CMVN Statistics
    families = trace.madeSPFamiliesAt(cmvnNode).families
    cmvnN = list()
    cmvnXTotal = list()
    cmvnSTotal = list()
    for z,count in sorted(tableCounts.iteritems()):
      aux = trace.madeSPAuxAt(trace.valueAt(families['[Atom(%d)]' % z]).makerNode).copy()
      cmvnN.append(aux.N)
      cmvnXTotal.append(aux.xTotal)
      cmvnSTotal.append(aux.STotal)
    rst['cmvnN'].append(cmvnN)
    rst['cmvnXTotal'].append(cmvnXTotal)
    rst['cmvnSTotal'].append(cmvnSTotal)

    # Save zs.
    if (i + 1) % Tzs == 0:
      print "Saving zs..."
      tic = time.clock()
      zs = [next(iter(trace.scopes['z'][n])).value.atom for n in xrange(N)]
      rst['ts_zs'].append(i)
      rst['zs'].append(zs)
      print 'zCounts:'
      print tableCounts.values()

    # Do prediction.
    if (i + 1) % Tpred == 0:
      print "Predicting..."
      tic = time.clock()
      y_pred = list()
      z_pred = list()
      for n in xrange(N, N + Ntst):
        v.observe('(x %d)' % n, \
                  {'type': 'list', \
                   'value': [{'type': 'real', 'value': x} for x in Xtst[n - N]]}, \
                  label='to_forget')
        v.infer('(gibbs z %d 1)' % n)
        y_pred.append(v.sample('(y %d (array %s))' % (n, ' '.join(repr(x) for x in Xtst[n - N]))))
        z_pred.append(v.sample('(z %d)' % n))
        v.forget('to_forget')
      t_pred_cum += time.clock() - tic
      acc = np.mean(np.array(y_pred) == ytst)

      # More record.
      rst['iters_pred'].append(i)
      rst['ts_pred'].append(t_pred_cum)
      rst['zs_pred'].append(z_pred)
      rst['ys_pred'].append(y_pred)
      rst['acc'].append(acc)
      print "Accuracy:", acc

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
  parser.add_argument('--data', dest='data_source_', default='four_cluster', help='data file')
  parser.add_argument('--eps',dest='epsilon_', default=0.0, type=float, help='Epsilon')
  parser.add_argument('--N',dest='N_', default=0, type=int, help='N')
  args = vars(parser.parse_args())
  main(**args)

