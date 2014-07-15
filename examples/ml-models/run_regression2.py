'''
Runs regression on a real data set; shows log score, time, generalization error
'''

from __future__ import division
import re
from venture.shortcuts import (make_puma_church_prime_ripl,
                               make_lite_church_prime_ripl)
from venture.unit import Analytics, MRipl
import numpy as np, scipy as sp, pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns
from os import path
from multiprocessing import Pool
import os
import cPickle as pkl
import sys
from sklearn import datasets
from venture.lite.psp import DeterministicPSP
from time import time

def load_model(infile):
  with open(infile) as f:
    lines = [x.strip() for x in f.readlines()]
  pass_next = False
  res = []
  for counter, line in enumerate(lines):
    pass_this = pass_next
    pass_next = False
    if pass_this:
      continue
    if re.match('^;', line) or not line:
      continue
    if 'assume D' in line:
      D = int(line.split(' ')[2][:-1])
    if line == '...':
      pass_next = True
      # get the previous line, and loop
      nextline = lines[counter+1]
      fmt_string = nextline.replace('D', '{i}')
      for i in range(2, D + 1):
        res.append(fmt_string.format(i = i))
    elif '...' in line:
      symbol = line.split()[1]
      replacement = ' '.join([symbol + '_' + str(i) for i in range(2, D + 1)])
      newline = line.replace('...', replacement).replace(' ' + symbol + '_D', '')
      res.append(newline)
    else:
      res.append(line)
  res = '\n'.join(res)
  return res

def build_ripl(infile = 'regression2.vnt', mripl = False, no_ripls = 1):
  model = load_model(infile)
  if mripl:
    r = MRipl(no_ripls = no_ripls, backend = 'lite', local_mode = False)
  else:
    r = make_lite_church_prime_ripl()
  r.load_prelude()
  _ = r.execute_program(model)
  return r

def get_data():
  data = datasets.load_boston()
  X = pd.DataFrame(data['data'], columns = data['feature_names'][:-1])
  X['INTERSECT'] = 1
  cols = list(X.columns)
  cols.remove('INTERSECT')
  X = X[['INTERSECT'] + cols]
  y = pd.Series(data['target'], name = data['feature_names'][-1])
  test_idx = np.sort(np.random.permutation(X.index)[:100])
  train_idx = np.setdiff1d(X.index.values, test_idx)
  return X.loc[test_idx], X.loc[train_idx], y.loc[test_idx], y.loc[train_idx]

def get_fantasy_data(datafile = 'regression-evolution2/data.pkl'):
  with open(datafile) as f:
    data = pkl.load(f)
  return data['X_test'], data['X_train'], data['y_test'], data['y_train']

def make_fantasy_data(infile = 'regression2.vnt'):
  r = build_ripl(infile)
  _ = r.forget('sigma_2')
  _ = r.assume('sigma_2', 0.5, label = 'sigma_2')
  _ = r.forget('w')
  _ = r.assume('w', '(vector 10 -8)', label = 'w')
  _ = r.assume('mem_unif', '(mem (lambda (i) (uniform_continuous -1 1)))')
  _ = r.assume('simulate', '(lambda (i) (list (vector 1 (mem_unif i)) (y (vector 1 (mem_unif i)))))')
  X_train = []
  y_train = []
  for i in range(20):
    thisone = r.sample('(simulate {0})'.format(i))
    X_train.append(thisone[0])
    y_train.append(thisone[1])
  X_train = pd.DataFrame(X_train)
  y_train = pd.Series(y_train)
  X_test = []
  y_test = []
  for i in range(2):
    thisone = r.sample('(simulate {0})'.format(i))
    X_test.append(thisone[0])
    y_test.append(thisone[1])
  X_test = pd.DataFrame(X_test)
  y_test = pd.Series(y_test)
  return X_test, X_train, y_test, y_train
  # with open('regression-evolution2/data.pkl', 'wb') as f:
  #   pkl.dump({'X_train' : X_train, 'X_test' : X_test,
  #             'y_train' : y_train, 'y_test' : y_test}, f)

# make_fantasy_data()

def observe(r, X_train, y_train):
  for i in range(len(X_train)):
    x = X_train.iloc[i]
    y = y_train.iloc[i]
    obs = '(y (vector {0}))'.format(' '.join(map(str, x)))
    r.observe(obs, y)
  return r

def input_test(r, X_test, y_test):
  '''
  input the test set as a list of lists so we can compute generalization error
  '''
  test = []
  for i in range(len(X_test)):
    x = X_test.iloc[i]
    y = y_test.iloc[i]
    test.append('(list (vector {0}) {1})'.format(' '.join(map(str, x)), y))
  assume_str = '(list ' + ' '.join(test) + ')'
  r.assume('test_set', assume_str)
  return r

def generalization_error(r):
  r.execute_program('''
  [assume generalization_error_1
    (lambda (in_list)
      (pow (- (y (first in_list)) (first (rest in_list))) 2))]

  [assume generalization_error
    (lambda ()
      (sqrt (mean (map generalization_error_1 test_set))))]''')
  return r

def compare_mripl_vs_resample(mripl, no_ripls):
  '''
  Compare speed of mripl to speed of just running infer resample
  '''
  print mripl
  # build it
  start = time()
  r = build_ripl(mripl = mripl, no_ripls = no_ripls)
  build_time = time() - start
  print 'build_time: ' + str(build_time)
  X_test, X_train, y_test, y_train = make_fantasy_data()
  r = input_test(r, X_test, y_test)
  start = time()
  r = observe(r, X_train, y_train)
  observe_time = time() - start
  print 'observe time: ' + str(observe_time)
  r = generalization_error(r)
  if not mripl:
    r.infer('(resample {0})'.format(no_ripls))
  infer_command = '(hmc default one 0.1 5 5)'
  plot_command = '(plotf (pcdtd ls l0 l3 l2 p1d2ds) (generalization_error) w_1 w_2 sigma_2)'
  cycle_command = '(cycle ({0} {1}) 5)'.format(infer_command, plot_command)
  start = time()
  res = r.infer(cycle_command)
  infer_time = time() - start
  print 'infer time: ' + str(infer_time)
  print

# compare_mripl_vs_resample(False, 50)
# compare_mripl_vs_resample(True, 50)

def runme(eps):
  print 'runnng with eps = ' + str(eps)
  r = build_ripl()
  r.forget('sigma_2')
  r.assume('sigma_2', 0.5)
  X_test, X_train, y_test, y_train = make_fantasy_data()
  r = input_test(r, X_test, y_test)
  r = observe(r, X_train, y_train)
  r = generalization_error(r)
  # r.force('sigma_2', 6.0)
  r.force('w_1', -7.0)
  r.force('w_2', 5.0)
  # infer_command = ('(cycle ((nesterov (quote weights) 1 0.1 5 5) (nesterov (quote weights) 2 0.1 5 5) (nesterov (quote sigma_2) 0 0.1 5 5)) 5)')
  # infer_command = ('(cycle ((hmc (quote weights) 1 0.01 5 5) (hmc (quote weights) 2 0.01 5 5) (hmc (quote sigma_2) 0 0.05 5 5)) 5)')
  # infer_command = ('(cycle ((mh (quote weights) 1 1) (mh (quote weights) 2 1) (mh (quote sigma_2) 0 1)) 10)')
  # infer_command = '(mh default one 50)'
  # infer_command = '(hmc default one 0.1 5 10)'
  infer_command = '(nesterov default one {0:0.1f} 10 20)'.format(eps)
  # infer_command = '(slice default one 20)'
  plotf_command = '(plotf (pts l0 l1 l2) w_1 w_2 sigma_2)'
  cycle_command = '(cycle ({0} {1}) 25)'.format(plotf_command, infer_command)
  res = r.infer(cycle_command)
  out = path.join('regression-results', 'nesterov_no_sigma_{0:0.1f}'.format(eps)).replace('.', '_')
  ds = res.dataset().set_index('sweeps')
  ds.to_csv(out + '.txt', sep = '\t', index = False, encoding = 'utf-8')
  fig, ax = plt.subplots(2,1)
  ds[['w_1', 'w_2', 'sigma_2']].plot(ax = ax[0])
  ds['log score'].plot(ax = ax[1])
  ax[0].set_title(infer_command)
  avg_time = ds['time (s)'].diff().mean()
  ax[1].set_title('Avg sweep time: {0:0.2f} s'.format(avg_time))
  ax[1].legend()
  fig.savefig(out + '.png')
  plt.close(fig)

runme(0.5)
# eps = np.r_[0.05:1.45:0.1]
# workers = Pool(14)
# workers.map(runme, eps)


