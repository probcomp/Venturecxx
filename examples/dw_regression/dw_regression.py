#! /usr/bin/env python

'''
Code to perform linear and logistic regression in Venture
'''

from __future__ import division
from venture.unit import MRipl, Analytics
from abc import ABCMeta, abstractmethod
import numpy as np, scipy as sp, pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns
from numpy import random
from sklearn.metrics import roc_auc_score, mean_squared_error
from os import path
import os

class Regression(object):
  '''
  Base class to perform regression analysis and run diagnostics in Venture.
  '''
  __metaclass__ = ABCMeta
  default_range = [-10,10]
  simulate_seed = 10003
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
    if hypers is None: hypers = self.default_hypers
    self.model_settings = {}
    self.p = p
    self.r.assume('p', p)
    for name in ['vector_w', 'hypers']:
      self.model_settings[name] = eval(name)
    # the priors
    for hyper in hypers:
      _ = self.r.assume(hyper, hypers[hyper])

  def simulate_data(self, n_train, n_test, input_range = None, seed = None):
    '''
    Simulate data from the model.

    Parameters
    ----------
    n_train : Number of training data points to make
    n_test : Number of test data points to make
    input_range : Inputs are generated uniformly over a possible range in each
      dimension. If None, left to class default.
    seed : Want the same seed for each simulated data set so we can make fair
      comparisons between runs. Seed doesn't matter, just a big nuber since
      the MRipls by default have seeds range(n_ripls)

    Returns
    -------
    Creates self.data, a dict with the simulated data.
    '''
    if seed is None: seed = self.simulate_seed
    # Randomly initialize a single ripl, use it to get model params
    m = type(self)(self.r.backend, 1, True)
    m.r.mr_set_seeds([seed])
    # grab the parameters
    m.build_model(self.p, self.model_settings['vector_w'],
                  self.model_settings['hypers'])
    # grab the model parameters from this new ripl
    self.data = {}
    self.data['w'] = m.r.predict('w')[0]
    if isinstance(m, LinearRegression):
      self.data['sigma_2'] = m.r.predict('sigma_2')[0]
    # make some fantasy x data, evaluate the y's based on model
    npts = n_train + n_test
    X = self._generate_inputs(m, npts, input_range)
    y = self._generate_outputs(m, X)
    self.data['X_train'], self.data['X_test'] = X[:n_train], X[n_train:]
    self.data['y_train'], self.data['y_test'] = y[:n_train], y[n_train:]
    self._observe_data()
    self.data['logscore'] = m.r.get_global_logscore()[0]
    # if logistic regression, compute the class membership probabilities
    if isinstance(self, LogisticRegression):
      self.data['prob_train'] = self._compute_probs(m, self.data['X_train'])
      self.data['prob_test'] = self._compute_probs(m, self.data['X_test'])

  def _generate_inputs(self, m, npts, input_range):
    '''
    Generate x inputs for simulated data. For linear regression, just choose
    uniformly on a grid. By defualt just [-10, 10] in each dimension; can
    change by changing input_range.
    For logistic regression, a little trickier because if
    you choose wrong you'll get all probabilities close to 0 or 1. Seems
    to work ok if I draw from Gaussian with variance equal to the variance on
    the prior for w, divided by the square root of the number of dimensions.
    '''
    # TODO: make this more intelligent for logistic regression
    # if they give an input range, us it
    if isinstance(self, LinearRegression):
      if input_range is None: input_range = self.default_range
      return random.uniform(*input_range, size = [npts, self.p])
    else:
      alpha = self.model_settings['hypers']['alpha']
      adjustment = np.sqrt(self.p)
      return np.random.normal(0, np.sqrt(alpha / adjustment),
                              size = [npts, self.p])

  def _generate_outputs(self, m, X):
    '''
    Make random outputs for each input
    '''
    y = []
    for x in X:
      y.append(m.r.predict('(y {0})'.format(self.to_vector(x))))
    return np.array(y)

  def _observe_data(self):
    '''
    Observe the data points we just generated
    '''
    for x, y in zip(self.data['X_train'], self.data['y_train']):
      _ = self.r.observe('(y {0})'.format(self.to_vector(x)), y[0])

  def evaluate_inference(self, nsteps, infer):
    '''
    Method to evaluate the quality of inference. Must run simulate_data
    before this so we have something to condition on, Right now, stores the
    following:
    -Run time for each inference step
    -Distance from mean of posterior distribution over w and true value at
      each step (this is clearly a heuristic, but this distance should decrease
      with more sampling).
    -The global log score (also keep the global log score for the actual data)
    -For linear regression, ditto above for the noise variance
    -Generalization error (root mean square prediction error for linear
      regresion, AOC for logistic regression)
    '''
    self.model = Analytics(self.r, queryExps = self._generate_query_exps())
    self.history, r_new = self.model.runFromConditional(sweeps = nsteps,
                                                        runs = self.r.no_ripls,
                                                        infer = infer)
    self.inference_results = self._collect_results()
    self.prediction_error = self._get_prediction_error()

  def _generate_query_exps(self):
    '''
    Make Analytics sample all the values of x_test
    '''
    querystr = ('(y {0})' if isinstance(self, LinearRegression)
                else '(prob {0})')
    return [querystr.format(self.to_vector(x)) for x in self.data['X_test']]

  def _collect_results(self):
    '''
    Put the history results in a nice form
    '''
    results = {}
    for key in self.model_params + ['logscore', 'sweep time (s)']:
      results[key] = self._collect_result(self.history.nameToSeries[key])
    return results

  @staticmethod
  def _collect_result(series):
    '''
    Collect results for a single series
    '''
    return pd.DataFrame([x.values for x in series]).T

  def _get_prediction_error(self):
    '''
    Computes prediction error.
    '''
    pred = self._get_predictions()
    res = []
    for step in pred.columns:
      this_step = pred[step]
      truth = self.data['y_test']
      res.append(eval(self.errorfun)(truth, this_step))
    return pd.Series(res)

  def _get_predictions(self):
    '''
    Grab the predicted values for all members of X_test; take the mean
    over the ripl's
    '''
    pred = []
    for query_exp in self._generate_query_exps():
      pred.append(self._collect_result(self.history.nameToSeries[query_exp]).
                  mean(axis = 1))
    res = pd.DataFrame(pred)
    res.index.name = ('y_test' if isinstance(self, LinearRegression)
                      else 'prob_test')
    res.columns.name = 'time_step'
    return res

  def _build_w(self, vector_w):
    '''
    Helper to make the prior weight matrix
    '''
    # linear regression multiplies by sigma_2, logistic doesn't
    variance = ('(* sigma_2 alpha)' if isinstance(self, LinearRegression)
                else 'alpha')
    if vector_w:
      # allocate as a single vector
      _ = self.r.assume('V_0', '(diag_matrix p {0})'.format(variance))
      w = ('(scope_include (quote weights) 0 (multivariate_normal {0} V_0))'.
           format(self.zeros(self.p)))
      _ = self.r.assume('w', w)
    else:
      _ = self.r.assume('V_0', variance)
      # loop over the entries and allocate one at a time; then aggregate
      for i in range(self.p):
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
  errorfun = 'mean_squared_error'
  model_params = ['w', 'sigma_2']
  default_hypers = {'a_0' : 1, 'b_0' : 1, 'alpha' : 1}
  def build_model(self, p, vector_w = True, hypers = None):
    '''
    Defines a Bayesian linear regression model. Notation follows Murphy, section
    7.6.3. p(y|x, w, sigma_2) = N(y|x * w, sigma_2). w and sigma_2 are assigned
    a normal-inverse-gamma prior, where sigma_2 is inverse-gamma(a_0, b_0) and
    w is multivariate normal with covariance V_0 = sigma_2 * alpha * I, where I
    is the identity and alpha is another prior parameter provided by user.

    Parameters
    ----------
    p, vector_w : Described in Regression class.

    hypers : Dict of hyperparameters.
      If None, set to default values.
      a_0, b_0: Parameters on the inverse-gamma prior for the noise variance
      sigma_2.
      alpha : If vector_w is True, assume spherical mean-0 Gaussian prior for w,
        with variance sigma_2 * alpha (so w and sigma_2 are normal-inverse-gamma).
        Else alpha is just the variance of the individual normal distributions.
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
  errorfun = 'roc_auc_score'
  model_params = ['w']
  default_hypers = {'alpha' : 1}
  def build_model(self, p, vector_w = True, hypers = None):
    '''
    Defines Bayesian logistic regression model, following Murphy 8.4.
    We have p(y|x,w) = Bernoulli(y|logistic(w * x)). w is assigned a multivariate
    Gaussian prior with covariance V_0 = alpha * I, where again alpha is supplied
    by the user.

    hypers : Dict of hyperparameters. If None, set to defaults.
      alpha : If vector_w is True, assume spherical mean-0 Gaussian prior on w
        with variance alpha. Else alpha is the individual variance on each weight.
    '''
    Regression.build_model(self, p, vector_w, hypers)
    # build the matrix of weights
    self._build_w(vector_w)
    # now the function for y
    _ = self.r.assume('prob', '(lambda (x) (logistic (dot x w)))')
    _ = self.r.assume('y', '(lambda (x) (bernoulli (prob x)))')

  def _compute_probs(self, m, X):
    '''
    Compute probabilities of membership
    '''
    y = []
    for x in X:
      y.append(m.r.sample('(prob {0})'.format(self.to_vector(x))))
    return np.array(y)

