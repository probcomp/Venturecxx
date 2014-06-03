## Subsampled MH for Joint DP Mixture of Logistic Regression Experts

import numpy as np
import scipy.io
import time
import shelve
from venture.shortcuts import make_lite_church_prime_ripl
make_ripl = make_lite_church_prime_ripl

def main(data_source_):
  ##########################################
  #### Parameters

  print "data_source:", data_source_

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
    ##### MNIST Mini Data
    from load_data import loadData
    data_file = 'data/input/mnist_D50_7_9_mini.mat'
    N, D, X, y, Ntst, Xtst, ytst = loadData(data_file)
    print "N:", N, "Ntst:", Ntst, "D:", D
  elif data_source == "circle":
    ##### Synthetic Circle Data
    from load_data import loadData
    data_file = 'data/input/circle_data.mat'
    N, D, X, y, Ntst, Xtst, ytst = loadData(data_file)

    # DEBUG
    N = 1000

    print "N:", N, "Ntst:", Ntst, "D:", D
  else:
    assert False


  ## Model
  # Hyper-param for the conjugate prior of mu_x
  m0 = np.zeros(D) # \mu_0 # Not used in venture
  k0 = 5 # m
  # Hyper-param for the conjugate prior of Sigma_x
  v0 = D + 5 # n_0, must be larger than D
  S0 = np.eye(D) * v0 # Psi # Not used in venture
  # Hyper-param for the Gamma prior of the CRP concentration
  a_alpha = 3 # 1
  b_alpha = 1

  ## Sampler
  time_max = 1e5
  T = 100000
  Tthin = 1
  Nsamples = (T + Tthin - 1) / Tthin

  Tzs = 100

  Tsave = 100

  # Number of Gibbs steps for z every iteration
  #step_z = round(N / 100)
  # DEBUG
  step_z = 100

  # jointdplr_mnist_mh or jointdplr_mnist_submh
  tag = "_".join(["dpgmm", data_source])

  stage_file = 'data/output/dpgmm/stage_'+tag
  result_file = 'data/output/dpgmm/result_'+tag

  ##########################################
  #### Initialization
  prog = """
  [clear]
  [assume D {D}]
  [assume m0 (zeros_array D)]
  [assume k0 {k0}]
  [assume v0 {v0}]
  [assume S0 (diagonal_matrix (scalar_product v0 (ones_array D)))]
  [assume alpha (scope_include (quote alpha) 0 (gamma {a_alpha!r} {b_alpha!r}))]
  [assume crp (make_crp alpha)]
  [assume z (mem (lambda (i) (scope_include (quote z) i (crp))))]
  [assume cmvn (mem (lambda (z) (make_cmvn m0 k0 v0 S0)))]
  [assume x (lambda (i) ((cmvn (z i))))]
  """.format(D = D, k0 = k0, v0 = v0, a_alpha = a_alpha, b_alpha = b_alpha)
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
  t_obs = time.clock() - tic
  print "It takes", t_obs, "seconds to load observations."

  ## Find CRP node and CMVN node
  trace = v.sivm.core_sivm.engine.getDistinguishedTrace()
  crpNode = trace.globalEnv.findSymbol('crp')
  #wNode = trace.globalEnv.findSymbol('w')
  tableCounts = trace.madeSPAuxAt(crpNode).tableCounts
  tables = tableCounts.keys()

  cmvnNode = trace.globalEnv.findSymbol('cmvn')

  rst = {'ts': list(),
         'alphas': list(),
         'zCounts': list(),
         'cmvnN': list(),
         'cmvnXTotal': list(),
         'cmvnSTotal': list(),
         'ts_zs': list(),
         'zs': list()}

  ##########################################
  #### Run and Record

  v.infer('(mh alpha all 1)') # First iteration to run engine.incorporate whose running time is excluded from record.

  t_start = time.clock()
  t_pred_cum = 0
  i_save = -1
  for i in xrange(Nsamples):
    # Run inference.
    infer_str = '(cycle ((gibbs z one {step_z}) (mh alpha all 1)) {Tthin})'.format(step_z = step_z, Tthin = Tthin)
    v.infer(infer_str)

    # Find z partition.
    tableCounts = trace.madeSPAuxAt(crpNode).tableCounts
    tables = tableCounts.keys()

    # Record.
    rst['ts'].append(time.clock() - t_start - t_pred_cum)
    rst['alphas'].append(v.sample('alpha'))
    zCountsTable = [[z, count] for z,count in sorted(tableCounts.iteritems())]
    rst['zCounts'].append(zCountsTable)

    # Save CMNV Statistics
    families = cmvnNode.madeSPFamilies.families
    cmvnN = list()
    cmvnXTotal = list()
    cmvnSTotal = list()
    for z,count in sorted(tableCounts.iteritems()):
      aux = trace.valueAt(families['[Atom(%d)]' % z]).makerNode.madeSPAux.copy()
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
  families = cmvnNode.madeSPFamilies.families
  auxDict = {}
  for (zStr, n) in families.iteritems():
    z = int(zStr[6:-2])
    aux = trace.valueAt(n).makerNode.madeSPAux.copy()
    auxDict[z] = aux
    print z, aux

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
  args = vars(parser.parse_args())
  main(**args)

