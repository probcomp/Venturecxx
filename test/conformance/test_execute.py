# Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

import math
from nose.tools import eq_

import venture.value.dicts as v
from venture.test.config import get_ripl, default_num_samples, default_num_transitions_per_sample, on_inf_prim
from venture.test.stats import statisticalTest, reportKnownGaussian

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
  return reportKnownGaussian(1, math.sqrt(0.5), predictions)

def testForgetSmoke():
  '''Check that execute_program does not break on labels and forgets'''
  ripl = get_ripl()
  prog = '''
  label : [ASSUME x 1]
  (forget 'label)'''
  ripl.execute_program(prog)

def testInferReturn():
  '''Make sure that execute_program returns results from infer commands'''
  ripl = get_ripl()
  prog = '[INFER (return (+ 5 3))]'
  ripl.infer('(resample 3)')
  res = ripl.execute_program(prog)[-1]['value']
  eq_(res, v.number(8.0))

def testCollectFunction():
  '''
  Make sure that calling collect on a function evaluation doesn't break
  '''
  ripl = get_ripl()
  ripl.assume('x', '(lambda() 2)')
  _ = ripl.infer('(do (mh default one 1) (collect (x)))')

def programString(infer):
  prog = '''
  [ASSUME mu (normal 0 1)]
  [ASSUME sigma (sqrt (inv_gamma 1 1))]
  [ASSUME x (lambda () (normal mu sigma))]
  [PREDICT (x)]'''
  prog += '\n' + infer
  return prog
