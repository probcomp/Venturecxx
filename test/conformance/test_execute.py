import math
from nose.tools import eq_
import scipy.stats
import numpy as np
from numpy.testing import assert_array_equal

from venture.test.config import get_ripl, default_num_samples, default_num_transitions_per_sample, on_inf_prim
from venture.test.stats import statisticalTest, reportKnownContinuous
from venture.engine.inference import SpecPlot

@on_inf_prim("mh")
@statisticalTest
def testExecuteSmoke():
  ripl = get_ripl()
  predictions = []
  for _ in range(default_num_samples()):
    ripl.clear()
    ripl.execute_program("""[assume x (normal 0 1)]
;; An observation
[observe (normal x 1) 2]
[infer (mh default one %s)]""" % default_num_transitions_per_sample())
    predictions.append(ripl.sample("x"))
  cdf = scipy.stats.norm(loc=1, scale=math.sqrt(0.5)).cdf
  return reportKnownContinuous(cdf, predictions, "N(1, sqrt(1/2))")

def testForget():
  '''Run this to make sure it doesn't break'''
  ripl = get_ripl()
  prog = '''
  label : [ASSUME x 1]
  [FORGET label]'''
  ripl.execute_program(prog)

def testPeekOutput():
  '''Make sure that execute_program returns results from peek commands'''
  ripl = get_ripl()
  prog = programString('[INFER (cycle ((peek mu sigma) (mh default one 5)) 5)]')
  ripl.infer('(resample 3)')
  res = ripl.execute_program(prog)[-1]['value']
  assert 'mu' in res.dataset()
  assert 'sigma' in res.dataset()
  eq_(res.dataset().shape[0], 15)
  assert_array_equal(res.dataset().particle.unique(), np.arange(3))

def testPeekFunction():
  '''
  Make sure that calling peak on a function evaluation doesn't break
  '''
  ripl = get_ripl()
  ripl.assume('x', '(lambda() 2)')
  res = ripl.infer('(cycle ((mh default one 1) (peek (x))) 1)')

def testPlotfOutput():
  '''Make sure that execute_program returns result form plotf commands'''
  ripl = get_ripl()
  prog = programString('[INFER (cycle ((plotf p0d1d mu sigma) (mh default one 5)) 5)]')
  res = ripl.execute_program(prog)[-1]['value']
  assert type(res.spec_plot) is SpecPlot
  assert 'mu' in res.dataset()
  assert 'sigma' in res.dataset()
  eq_(res.dataset().shape[0], 5)

def programString(infer):
  prog = '''
  [ASSUME mu (normal 0 1)]
  [ASSUME sigma (sqrt (inv_gamma 1 1))]
  [ASSUME x (lambda () (normal mu sigma))]
  [PREDICT (x)]'''
  prog += '\n' + infer
  return prog
