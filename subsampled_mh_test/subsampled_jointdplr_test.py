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
    from load_data import loadData
    data_file = 'data/input/mnist_D50_7_9.mat'
    N, D, X, y, Ntst, Xtst, ytst = loadData(data_file)
    print "N:", N, "Ntst:", Ntst, "D:", D
  elif data_source == "mnist_mini":
    ##### MNIST Data
    from load_data import loadData
    data_file = 'data/input/mnist_D50_7_9_mini.mat'
    N, D, X, y, Ntst, Xtst, ytst = loadData(data_file)
    print "N:", N, "Ntst:", Ntst, "D:", D
  elif data_source == "circle":
    ##### MNIST Data
    from load_data import loadData
    data_file = 'data/input/circle_data.mat'
    N, D, X, y, Ntst, Xtst, ytst = loadData(data_file)
    print "N:", N, "Ntst:", Ntst, "D:", D
  else:
    assert False


  ## Model
  # Hyper-param for w
  Sigma_w = np.sqrt(0.1)
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

  Tpred = 100

  Tsave = 100

  # Proposal
  sig_prop = 0.01

  # Austerity
  Nbatch = 50
  k0 = 3
  epsilon = epsilon_

  use_austerity = epsilon != 0 # False # True
  tag_austerity = "submh_%.2f" % epsilon if use_austerity else "mh"

  # Number of Gibbs steps for z every iteration
  if use_austerity:
    step_z = round(N / 100)
  else:
    step_z = round(N / 100)
  step_z = max(1, step_z)

  #DEBUG
  step_z = 1

  # jointdplr_mnist_mh or jointdplr_mnist_submh
  tag = "_".join(["jointdplr_test", data_source, tag_austerity])

  stage_file = 'data/output/jointdplr/stage_'+tag
  result_file = 'data/output/jointdplr/result_'+tag

  ##########################################
  #### Initialization
  prog = """
  [clear]
  [assume D {D}]
  [assume mu_w (zeros_array (+ D 1))]
  [assume Sigma_w (diagonal_matrix (scalar_product {Sigma_w!r} (ones_array (+ D 1))))]
  [assume m0 (zeros_array D)]
  [assume k0 {k0}]
  [assume v0 {v0}]
  [assume S0 (diagonal_matrix (scalar_product v0 (ones_array D)))]
  [assume alpha (scope_include (quote alpha) 0 (gamma {a_alpha!r} {b_alpha!r}))]
  [assume crp (make_crp alpha)]
  [assume z (mem (lambda (i) (scope_include (quote z) i (crp))))]
  [assume w (mem (lambda (z) (scope_include (quote w) z (multivariate_normal mu_w Sigma_w))))]
  [assume cmvn (mem (lambda (z) (make_cmvn m0 k0 v0 S0)))]
  [assume x (lambda (i) ((cmvn (z i))))]
  [assume y (lambda (i x) (bernoulli (linear_logistic (w (z i)) x)))]
  """.format(D = D, Sigma_w = Sigma_w, k0 = k0, v0 = v0, a_alpha = a_alpha, b_alpha = b_alpha)
  v = make_ripl()
  v.execute_program(prog);

  ## Load observations.
  tic = time.clock()
  for n in xrange(N):
    if (n + 1) % round(N / 10) == 0:
      print "Processing %d/%d observations." % (n + 1, N)
    v.observe('(x %d)' % n, \
              {'type': 'list', \
               'value': [{'type': 'real', 'value': x} for x in X[n]]})
    v.observe('(y %d (array %s))' % (n, ' '.join(repr(x) for x in X[n])), y[n])
  t_obs = time.clock() - tic
  print "It takes", t_obs, "seconds to load observations."

  ## Find CRP node
  trace = v.sivm.core_sivm.engine.getDistinguishedTrace()
  crpNode = trace.globalEnv.findSymbol('crp')
  #wNode = trace.globalEnv.findSymbol('w')
  tableCounts = trace.madeSPAuxAt(crpNode).tableCounts
  tables = tableCounts.keys()

  rst = {'ts': list(),
         'alphas': list(),
         'zCounts': list(),
         'ws': list(),
         'iters_pred': list(),
         'ts_pred': list(),
         'ys_pred': list()}

  ##########################################
  #### Run and Record

  v.infer('(mh alpha all 1)') # First iteration to run engine.incorporate whose running time is excluded from record.

  t_start = time.clock()
  t_pred_cum = 0
  i_save = -1
  for i in xrange(Nsamples):
    # Run inference.
    if not use_austerity:
      infer_str = '(cycle (' + \
          ' '.join(['(mh w {z} 1 true {sig_prop})'.format(\
              z = z, sig_prop = sig_prop) for z in tables]) + ' ' + \
          '(gibbs z one {step_z}) (mh alpha all 1)) {Tthin})'.format(\
              step_z = step_z, Tthin = Tthin)
    else:
      infer_str = '(cycle (' + ' '.join([\
          '(subsampled_mh w {z} 1 {Nbatch} {k0} {epsilon} true {sig_prop} true)'.format(\
              z = z, Nbatch = Nbatch, k0 = k0, epsilon = epsilon, \
              sig_prop = sig_prop) for z in tables]) + ' ' + \
          '(gibbs z one {step_z} true true) (mh alpha all 1)) {Tthin})'.format(\
              step_z = step_z, Tthin = Tthin)

    v.infer(infer_str)

    # Find z partition.
    tableCounts = trace.madeSPAuxAt(crpNode).tableCounts
    tables = tableCounts.keys()

    # Record.
    rst['ts'].append(time.clock() - t_start - t_pred_cum)
    rst['alphas'].append(v.sample('alpha'))
    zCountsTable = [[z, count] for z,count in sorted(tableCounts.iteritems())]
    rst['zCounts'].append(zCountsTable)
    rst['ws'].append([np.array(v.sample('(w {z})'.format(z=z[0]))) for z in zCountsTable])

    # Do prediction.
    if (i + 1) % Tpred == 0:
      print "Predicting..."
      tic = time.clock()
      y_pred = list()
      for n in xrange(N, N + Ntst):
        v.observe('(x %d)' % n, \
                  {'type': 'list', \
                   'value': [{'type': 'real', 'value': x} for x in Xtst[n - N]]}, \
                  label='to_forget')
        v.infer('(gibbs z %d 1)' % n)
        y_pred.append(v.sample('(y %d (array %s))' % (n, ' '.join(repr(x) for x in Xtst[n - N]))))
        v.forget('to_forget')
      t_pred_cum += time.clock() - tic

      # More record.
      rst['iters_pred'].append(i)
      rst['ts_pred'].append(t_pred_cum)
      rst['ys_pred'].append(y_pred)

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

  ## Plotting.
  #figure()
  #plot(rst_mh['ts'], 'x-')
  #figure()
  #plot(rst_mh['ts'], rst_mh['alphas'], 'x-')
  #figure()
  #plot([len(z_count) for z_count in rst_mh['zCounts']])

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
  parser.add_argument('--data', dest='data_source_', default='circle', help='data file')
  parser.add_argument('--eps',dest='epsilon_', default=0.0, type=float, help='Epsilon')
  args = vars(parser.parse_args())
  main(**args)

