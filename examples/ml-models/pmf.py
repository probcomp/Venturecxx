'''
Run probabilistic matrix factorization on a toy dataset and on the MovieLens
100k dataset
'''
from os import path
import numpy as np, pandas as pd
from venture.lite import psp
from venture.unit import VentureUnit
from venture.shortcuts import make_lite_church_prime_ripl
from venture.lite.builtin import typed_nr
from venture.lite import value as v
from venture.lite.builtin import deterministic_typed

def get_data(ntrain = None, ntest = None):
  '''
  If ntrain and ntest given, truncate the data sets to contain ntrain, ntest rows.
  '''
  data_path = path.expanduser('~/Google Drive/probcomp/pmf/ml-100k/')
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

class CrossValPSP(psp.RandomPSP):
  '''
  Custom inference SP to perform cross-validation on holdout set.
  Accepts the holdout set as a nested list whose elements are
  user_id / item_id / rating triples
  '''
  def canAbsorb(self, _trace, _appNode, _parentNode):
    return False

  def simulate(self, args):
    # need to implement
    pass

def build_bayes_ripl(ripl):
  prog = '''
  [ASSUME mu_0 (repeat 0 D)]
  [ASSUME nu_0 D]
  [ASSUME beta_0 1]
  [ASSUME W_0 (id_matrix D)]
  [ASSUME Sigma_U (inv_wishart W_0 nu_0)]
  [ASSUME mu_U (multivariate_normal mu_0 (scalar_mult beta_0 Sigma_U))]
  [ASSUME Sigma_V (inv_wishart W_0 nu_0)]
  [ASSUME mu_V (multivariate_normal mu_0 (scalar_mult beta_0 Sigma_V))]'''
  ripl.execute_program(prog)
  return ripl

def build_nonbayes_ripl(ripl):
  prog = '''
  [ASSUME sigma_2_u 250]
  [ASSUME sigma_2_v 250]
  [ASSUME Sigma_U (scalar_mult sigma_2_U (id_matrix D))]
  [ASSUME mu_U (repeat 0 D)]
  [ASSUME Sigma_V (scalar_mult sigma_2_V (id_matrix D))]
  [ASSUME mu_V (repeat 0 D)]'''
  ripl.execute_program(prog)
  return ripl

def build_ripl(bayes = True):
  ripl = make_lite_church_prime_ripl()
  scalar_mult = deterministic_typed(np.dot,
                                    [v.NumberType(), v.MatrixType()],
                                    v.MatrixType())
  ripl.bind_foreign_sp('scalar_mult', scalar_mult)
  prog = '''
  [ASSUME D 10]
  [ASSUME sigma_2 (/ 1 2)]'''
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
          multivariate_normal mu_U Sigma_U))))]
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
          (sqrt sigma_2))))]
  [ASSUME crossval_predict
    (lambda (test)
      (map (lambda (x)
             (make_R (lookup x 0) (lookup x 1)))
           test))]'''
  ripl.execute_program(prog)
  crossval_sp = typed_nr(CrossValPSP(), [v.ListType()], v.NumberType())
  ripl.bind_foreign_sp('crossval', crossval_sp)
  return ripl


def main():
  ripl = build_ripl(bayes = True)


