'''
Run probabilistic matrix factorization on a toy dataset and on the MovieLens
100k dataset
'''
from os import path
import numpy as np, pandas as pd
from venture.lite import value as v
from venture.unit import Analytics
from venture.shortcuts import make_lite_church_prime_ripl
from venture.lite.builtin import deterministic_typed
from time import time

def get_data(ntrain = None, ntest = None, data_path = 'pmf-example-data'):
  '''
  If ntrain and ntest given, truncate the data sets to contain ntrain, ntest rows.
  '''
  train = pd.read_table(path.join(data_path, 'ua.base'), header = 0,
                        names = ['user_id', 'item_id', 'rating', 'timestamp'])
  del train['timestamp']
  if ntrain is not None: train = train[:ntrain]
  test = pd.read_table(path.join(data_path, 'ua.test'), header = 0,
                        names = ['user_id', 'item_id', 'rating', 'timestamp'])
  del test['timestamp']
  if ntest is not None: test = test[:ntest]
  return train, test

def format_test(test):
  x = ['(vector {0} {1})'.format(x['user_id'], x['item_id']) for _, x in test.iterrows()]
  return '(list {0})'.format(' '.join(x))

def build_bayes_ripl(ripl):
  prog = '''
  [ASSUME mu_0 (repeat 0 D)]
  [ASSUME nu_0 D]
  [ASSUME beta_0 1]
  [ASSUME W_0 (id_matrix D)]
  [ASSUME Sigma_U (inv_wishart W_0 nu_0)]
  [ASSUME mu_U (multivariate_normal mu_0 (scalar_by_mat_mult beta_0 Sigma_U))]
  [ASSUME Sigma_V (inv_wishart W_0 nu_0)]
  [ASSUME mu_V (multivariate_normal mu_0 (scalar_by_mat_mult beta_0 Sigma_V))]'''
  ripl.execute_program(prog)
  return ripl

def build_nonbayes_ripl(ripl):
  prog = '''
  [ASSUME sigma_2_U 250]
  [ASSUME sigma_2_V 250]
  [ASSUME Sigma_U (scalar_by_mat_mult sigma_2_U (id_matrix D))]
  [ASSUME mu_U (repeat 0 D)]
  [ASSUME Sigma_V (scalar_by_mat_mult sigma_2_V (id_matrix D))]
  [ASSUME mu_V (repeat 0 D)]'''
  ripl.execute_program(prog)
  return ripl

def build_ripl(bayes = True, D = 10):
  ripl = make_lite_church_prime_ripl()
  ripl.load_prelude()
  scalar_by_mat_mult = deterministic_typed(np.dot,
                                    [v.NumberType(), v.MatrixType()],
                                    v.MatrixType())
  ripl.bind_foreign_sp('scalar_by_mat_mult', scalar_by_mat_mult)
  prog = '''
  [ASSUME D {0}]
  [ASSUME sigma_2 (/ 1 2)]'''.format(D)
  ripl.execute_program(prog)
  if bayes:
    ripl = build_bayes_ripl(ripl)
  else:
    ripl = build_nonbayes_ripl(ripl)
  prog = '''
  [ASSUME make_U
    (mem
      (lambda (user)
        (scope_include (quote U) user
          (multivariate_normal mu_U Sigma_U))))]
  [ASSUME make_V
    (mem
      (lambda (movie)
        (scope_include (quote V) movie
          (multivariate_normal mu_V Sigma_V))))]
  [ASSUME make_R
    (mem
      (lambda (user movie)
        (normal
          (vector_dot (make_U user) (make_V movie))
          (sqrt sigma_2))))]'''
  ripl.execute_program(prog)
  return ripl

def load_data(ripl, ntrain = None, ntest = None):
  train, test = get_data(ntrain, ntest)
  # make the observations
  for _, row in train.iterrows():
    obs = '(make_R {0} {1})'.format(row['user_id'], row['item_id'])
    ripl.observe(obs, row['rating'])
  # load in the validation data so we have it
  validation = []
  for _, row in test.iterrows():
    valstr = '(pair (vector {0} {1}) {2})'.format(row['user_id'], row['item_id'], row['rating'])
    validation.append(valstr)
  val = '(list {0})'.format(' '.join(validation))
  ripl.assume('data_val', val)
  return ripl

def define_prediction_error(ripl):
  prog = '''
  [ASSUME make_R_list
    (lambda (data)
      (make_R (lookup data 0) (lookup data 1)))]

  [ASSUME prediction_error
    (lambda ()
      (rmse_accuracy data_val make_R_list))]'''
  ripl.execute_program(prog)
  return ripl

def run_ripl():
  '''
  Run the model using the ripl interface.
  This breaks, with error "'float' object has no attribute 'number'"
  '''
  start = time()
  # ripl = build_ripl(bayes = True)
  ripl = build_ripl(bayes = False)
  ripl = define_prediction_error(load_data(ripl, ntrain = 100, ntest = 20))
  ripl.infer('(nesterov default one 0.08 10 1)')
  infer = '(cycle ((nesterov U all 0.08 10 10) (nesterov V all 0.08 10 10)  (plotf (ls l0) (prediction_error))) 5)'
  res = ripl.infer(infer)
  print time() - start
  return ripl, res

def run_analytics():
  '''
  Run the model using the analytics interface.
  This breaks, with error "unhashable type: 'dict'"
  '''
  start = time()
  ripl = build_ripl(bayes = True)
  ripl = define_prediction_error(load_data(ripl, ntrain = 100, ntest = 20))
  model = Analytics(ripl, queryExps = ['(prediction_error)'])
  history, ripl = model.runFromConditional(sweeps = 10,
                                           infer = '(mh deafault one 10)')
  return history, ripl

if __name__ == '__main__':
  run_ripl()
