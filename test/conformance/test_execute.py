import math
from nose.tools import eq_
import scipy.stats

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
  prog = programString('[INFER (cycle ((peek mu) (peek sigma) (mh default one 5)) 5)]')
  res = ripl.execute_program(prog)[-1]['value']
  eq_(set(res.keys()), {'mu', 'sigma'})
  eq_(len(res['mu']), 5)
  eq_(len(res['sigma']), 5)

def testPlotfOutput():
  '''Make sure that execute_program returns result form plotf commands'''
  ripl = get_ripl()
  prog = programString('[INFER (cycle ((plotf p0d1d mu sigma) (mh default one 5)) 5)]')
  res = ripl.execute_program(prog)[-1]['value']
  assert type(res) is SpecPlot

def programString(infer):
  prog = '''
  [ASSUME mu (normal 0 1)]
  [ASSUME sigma (sqrt (inv_gamma 1 1))]
  [ASSUME x (lambda () (normal mu sigma))]
  [PREDICT (x)]'''
  prog += '\n' + infer
  return prog
