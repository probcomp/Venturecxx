#! /usr/bin/env python

'''
Code to perform linear and logistic regression in Venture
'''

from venture.unit import MRipl, Analytics
from abc import ABCMeta, abstractmethod
import numpy as np
from numpy import random
import seaborn as sns

class Regression(object):
  '''
  Base class to perform regression analysis and run diagnostics in Venture.
  '''
  __metaclass__ = ABCMeta
  default_range = [-10,10]
  def __init__(self, backend, no_ripls = 1, local_mode = True):
    '''
    Parameters
    ----------
    backend : puma or lite
    no_ripls : The number of ripls controlled by the MRipl
    local_mode : If True, don't use IPCluster
    '''
    self.r = MRipl(backend = backend, no_ripls = no_ripls,
                   local_mode = local_mode)
    self.load_prelude()

  @abstractmethod
  def build_model(self, p, vector_w, hypers):
    '''
    Parameters
    ----------
    p : The number of dimensions

    vector_w : The manner in which to define the weight matrix. If True,
      draw w as a single vector from spherical multivariate Gaussian. Else,
      take p individual draws from univariate Gaussian. The difference is in
      the sampling.

    More info on hyperparameters in the descentant classes. Both descendants
    call this method, then do some more stuff of their own.
    '''
    # clear anything that's there now
    self.r.clear()
    self.load_prelude()
    # store model setttings
    self.model_settings = {}
    self.p = p
    self.r.assume('p', p)
    for arg in ['hypers', 'vector_w']:
      self.model_settings[arg] = eval(arg)
    # the priors
    if hypers is None: hypers = self.default_hypers
    for hyper in hypers:
      _ = self.r.assume(hyper, hypers[hyper])

  def simulate_data(self, n_train, n_test, input_range = None):
    '''
    Simulate data from the model.

    Parameters
    ----------
    n_train : Number of training data points to make
    n_test : Number of test data points to make
    input_range : Inputs are generated uniformly over a possible range in each
      dimension. If None, left to class default.

    Returns
    -------
    Creates self.data, a dict with the simulated data.
    '''
    # Randomly initialize a single ripl, use it to get model params
    m = type(self)(self.r.backend, 1, True)
    # grab the parameters
    m.build_model(self.p, self.model_settings['vector_w'], 
                  self.model_settings['hypers'])
    # grab the model parameters from this new ripl
    self.data = {}
    self.data['w'] = m.r.sample('w')[0]
    if isinstance(m, LinearRegression):
      self.data['sigma_2'] = m.r.sample('sigma_2')[0]
    # make some fantasy x data, evaluate the y's based on model
    npts = n_train + n_test
    X = self._generate_inputs(m, npts, input_range)
    y = self._generate_outputs(m, X)
    self.data['X_train'], self.data['X_test'] = X[:n_train], X[n_train:]
    self.data['y_train'], self.data['Y_test'] = y[:n_train], y[n_train:]
    self._observe_data()

  def load_data(self, dataset):
    '''
    Load data from 
    '''

  def _generate_inputs(self, m, npts, input_range):
    '''
    Generate x inputs for simulated data. For linear regression, just choose
    uniformly on a grid. For logistic regression, want to find a region where
    the probabilities aren't all 0 or 1.
    '''
    # TODO: make this more intelligent for logistic regression
    # if they give an input range, us it
    if input_range is not None:
      return random.uniform(*input_range, size = [npts, self.p])
    # if it's linear regression, just do the class default
    else:
      return random.uniform(*self.default_range, size = [npts, self.p])

  def _generate_outputs(self, m, X):
    '''
    Make random outputs for each input
    '''
    y = []
    for x in X:
      y.append(m.r.sample('(y {0})'.format(self.to_vector(x))))
    return np.array(y)

  def _observe_data(self):
    '''
    Observe the data points we just generated
    '''
    for x, y in zip(self.data['X_train'], self.data['y_train']):
      _ = self.r.observe('(y {0})'.format(self.to_vector(x)), y[0])

  def evaluate_inference(self, nsteps, inference):
    '''
    Method to evaluate the quality of inference. Must run simulate_data
    before this so we have something to condition on, Right now, stores the 
    following:
    -Run time for each inference step
    -Distance from mean of posterior distribution over w and true value at
      each step (this is clearly a heuristic, but this distance should decrease
      with more sampling).
    -For linear regression, ditto above for the noise variance
    -Generalization error (root mean square prediction error for linear
      regresion, AOC for logistic regression)
    '''
    pass

  def _build_w(self, vector_w):    
    '''
    Helper to make the prior weight matrix
    '''
    # linear regression multiplies by sigma_2, logistic doesn't
    variance = ('(* sigma_2 v_0)' if isinstance(self, LinearRegression)
                else 'v_0')
    if vector_w:
      # allocate as a single vector
      _ = self.r.assume('V_0', '(diag_matrix p {0})'.format(variance))
      w = ('(scope_include (quote weights) 0 (multivariate_normal {0} V_0))'.
           format(self.zeros(self.p)))
      _ = self.r.assume('w', w)
    else:
      _ = self.r.assume('V_0', variance)
      # loop over the entries and allocate one at a time; then aggregate
      for i in range(p):
        w_i = ('(scope_include (quote weights) {0} (normal 0 (sqrt V_0)))'.
               format(i))
        self.r.assume('w_' + str(i), w_i)
      w = '(vector '  + ' '.join(['w_' + str(i) for i in range(self.p)]) + ')'
      self.r.assume('w', w)

  @staticmethod
  def zeros(p):
    '''
    Make zero vector of length p
    '''
    return '(vector {0})'.format(('0 ' * p).strip())

  def load_prelude(self):
    '''
    Load useful functions I'll need.
    '''
    prog = '''
    [assume dot
      (lambda (x y)
        (dot_helper x y 0 (size x)))]

    [assume dot_helper
      (lambda (x y idx l)
        (if (= idx l)
          0
          (+
            (* (lookup x idx) (lookup y idx))
            (dot_helper x y (+ 1 idx) l))))]

    [assume logistic (lambda (x)
      (/ 1 (+ 1 (exp (- 0 x)))))]

    [assume diag_matrix 
      (lambda (p fill_value)
        (matrix (diag_matrix_helper p fill_value 0)))]

    [assume diag_matrix_helper
      (lambda (p fill_value idx)
        (if (= idx p)
          (list)
          (pair
            (fill_one p fill_value idx) 
            (diag_matrix_helper p fill_value (+ idx 1)))))]

    [assume fill_one
      (lambda (p fill_value fill_position)
        (fill_one_helper p fill_value fill_position 0))]

    [assume fill_one_helper
      (lambda (p fill_value fill_position idx)
        (if (= idx p)
          (list)
          (pair
            (if (= idx fill_position) fill_value 0)
            (fill_one_helper p fill_value fill_position (+ idx 1)))))]
    '''
    _ = self.r.execute_program(prog)

  @staticmethod
  def to_vector(v):
    '''
    Converts a list / numpy array to a string for a Venture array
    '''
    return '(vector {0})'.format(' '.join(map(str,v)))

from venture.shortcuts import (make_puma_church_prime_ripl,
                               make_lite_church_prime_ripl)

class LinearRegression(Regression):
  '''
  Bayesian linear regression
  '''
  # default parameters for the priors
  default_hypers = {'a_0' : 1, 'b_0' : 1, 'v_0' : 1}
  def build_model(self, p, vector_w = True, hypers = None):
    '''
    Defines a Bayesian linear regression model. Notation follows Murphy, section
    7.6.3. p(y|x, w, sigma_2) = N(y|x * w, sigma_2).

    Parameters
    ----------
    p, vector_w : Described in Regression class.

    hypers : Dict of hyperparameters. 
      If None, set to default values.
      a_0, b_0: Parameters on the inverse-gamma prior for the noise variance sigma_2.
      v_0 : If vector_w is True, assume spherical mean-0 Gaussian prior for w, 
        with variance sigma_2 * v_0 (so w and sigma_2 are normal-inverse-gamma).
        Else v_0 is just the variance of the individual normal distributions.
    '''
    # do the stuff common to linear and logistic regression
    Regression.build_model(self, p, vector_w, hypers)
    # noise precision
    sigma_2 = '(scope_include (quote noise) 0 (inv_gamma a_0 b_0))'
    _ = self.r.assume('sigma_2', sigma_2)
    # make the weights
    self._build_w(vector_w)
    # now the actual function for y
    y = '(lambda (x) (normal (dot x w) (sqrt sigma_2)))'
    _ = self.r.assume('y', y)

class LogisticRegression(Regression):
  '''
  Bayesian logistic regression
  '''
  # default parameters for the priors
  default_hypers = {'v_0' : 1}
  def build_model(self, p, vector_w = True, hypers = None):
    '''
    Defines Bayesian logistic regression model, following Murphy 8.4.

    hypers : Dict of hyperparameters. If None, set to defaults.
      v_0 : If vector_w is True, assume spherical mean-0 Gaussian prior on w
        with variance v_0. Else v_0 is the individual variance on each weight.
    '''
    Regression.build_model(self, p, vector_w, hypers)
    # build the matrix of weights
    self._build_w(vector_w)
    # now the function for y
    _ = self.r.assume('prob', '(lambda (x) (logistic (dot x w)))')
    _ = self.r.assume('y', '(lambda (x) (bernoulli (prob x)))')


if __name__ == '__main__':
  # before doing more, make sure this thing works
  self = LinearRegression(backend = 'puma', no_ripls = 8, local_mode = False)
  self.build_model(1, True, None)
  self.simulate_data(100, 20)
  print self.data['w'][0]
  print np.mean(self.r.sample('w'))
  # train = pd.DataFrame({'x' : self.simulated['X_train'].ravel(),
  #                       'y' : self.simulated['y_train'].ravel()})


  model = Analytics(self.r)

  # ok make sure we recover it in venture
  self.r.infer('(mh default one 100)')
  # for i in range(100):
  #   self.r.infer('(mh default one 100')


