'''
Runs regression on a real data set; shows log score, time, generalization error
'''

from __future__ import division
import re
from venture.shortcuts import (make_puma_church_prime_ripl,
                               make_lite_church_prime_ripl)
import numpy as np, scipy as sp, pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns
from os import path
import os
import cPickle as pkl
import sys
from sklearn import datasets
from venture.lite.psp import DeterministicPSP

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

def build_ripl(infile = 'regression2.vnt'):
  model = load_model(infile)
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

def runme():
  r = build_ripl()
  X_test, X_train, y_test, y_train = get_data()
  r = input_test(r, X_test, y_test)
  r = observe(r, X_train, y_train)
  r = generalization_error(r)
  infer_command = (' '.join(['(mh (quote weights) {0} 1)'.format(i) for i in range(1, 16)]) +
                   ' (mh (quote noise) 1 5)')
  plot_command = '(plotf (ls l0) generalization_error)'
  cycle_command = '(cycle ({0} {1}) 5)'.format(infer_command, plot_command)
  res = r.infer(cycle_command)


