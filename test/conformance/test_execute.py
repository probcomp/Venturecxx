import math
from nose.tools import eq_
import scipy.stats
import numpy as np
from numpy.testing import assert_array_equal

import venture.value.dicts as v
from venture.test.config import get_ripl, default_num_samples, default_num_transitions_per_sample, on_inf_prim
from venture.test.stats import statisticalTest, reportKnownContinuous

@on_inf_prim("mh")
@statisticalTest
def testExecuteSmoke():
  ripl = get_ripl()
  predictions = []
  for _ in range(default_num_samples()):
    ripl.clear()
    ripl.execute_program("""[assume x (normal 0 1)]
;; An observation
[observe (normal x 1) 2] ; with an end-of-line comment
[infer (mh default one %s)]""" % default_num_transitions_per_sample())
    predictions.append(ripl.sample("x"))
  cdf = scipy.stats.norm(loc=1, scale=math.sqrt(0.5)).cdf
  return reportKnownContinuous(cdf, predictions, "N(1, sqrt(1/2))")

def testForgetSmoke():
  '''Check that execute_program does not break on labels and forgets'''
  ripl = get_ripl()
  prog = '''
  label : [ASSUME x 1]
  [FORGET label]'''
  ripl.execute_program(prog)

def testInferReturn():
  '''Make sure that execute_program returns results from infer commands'''
  ripl = get_ripl()
  prog = '[INFER (return (+ 5 3))]'
  ripl.infer('(resample 3)')
  res = ripl.execute_program(prog)[-1]['value']
  eq_(res, v.number(8.0))

def testPeekFunction():
  '''
  Make sure that calling peek on a function evaluation doesn't break
  '''
  ripl = get_ripl()
  ripl.assume('x', '(lambda() 2)')
  _ = ripl.infer('(cycle ((mh default one 1) (peek (x))) 1)')

def programString(infer):
  prog = '''
  [ASSUME mu (normal 0 1)]
  [ASSUME sigma (sqrt (inv_gamma 1 1))]
  [ASSUME x (lambda () (normal mu sigma))]
  [PREDICT (x)]'''
  prog += '\n' + infer
  return prog
