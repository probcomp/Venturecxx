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

import scipy.stats as stats
import re
from StringIO import StringIO
import sys

from venture.test.stats import statisticalTest, reportKnownContinuous
from venture.test.config import get_ripl, default_num_samples, on_inf_prim
from venture.lite.psp import LikelihoodFreePSP
import venture.lite.types as t
from venture.lite.builtin import typed_nr

def extract_from_dataset(result, names):
  return result.asPandas()[names]

@statisticalTest
@on_inf_prim("collect") # Technically also MH, but not testing it
def testCollectSmoke1():
  ripl = get_ripl()
  ripl.assume("x", "(normal 0 1)")
  prog = """
(let ((d (empty)))
  (do (repeat %s
       (do (mh default one 1)
           (bind (collect x) (curry into d))))
      (return d)))""" % default_num_samples()
  predictions = extract_from_dataset(ripl.infer(prog), 'x')
  cdf = stats.norm(loc=0.0, scale=1.0).cdf
  return reportKnownContinuous(cdf, predictions, "N(0,1)")

@statisticalTest
@on_inf_prim("collect")
def testCollectSmoke2():
  ripl = get_ripl()
  prog = """
(let ((d (empty)))
  (do (repeat %s (bind (collect (normal 0 1)) (curry into d)))
      (return d)))""" % default_num_samples()
  predictions = extract_from_dataset(ripl.infer(prog), '(normal 0.0 1.0)')
  cdf = stats.norm(loc=0.0, scale=1.0).cdf
  return reportKnownContinuous(cdf, predictions, "N(0,1)")

@statisticalTest
@on_inf_prim("collect")
def testCollectSmoke3():
  ripl = get_ripl()
  prog = """
(let ((d (empty)))
  (do (repeat %s (bind (collect (labelled (normal 0 1) label)) (curry into d)))
      (return d)))""" % default_num_samples()
  predictions = extract_from_dataset(ripl.infer(prog), 'label')
  cdf = stats.norm(loc=0.0, scale=1.0).cdf
  return reportKnownContinuous(cdf, predictions, "N(0,1)")

@statisticalTest
@on_inf_prim("collect") # Technically also resample and MH, but not testing them
def testCollectSmoke4():
  # This is the example from examples/normal_plot.vnt
  ripl = get_ripl()
  ripl.infer("(resample 10)")
  ripl.assume("x", "(normal 0 1)")
  ripl.assume("y", "(normal x 1)")
  ripl.assume("abs", "(lambda (x) (if (< x 0) (- 0 x) x))")
  out = ripl.infer("""
(let ((d (empty)))
  (do (repeat 3
       (do (mh default all 1)
           (bind (collect x y (abs (- y x)) (labelled (abs x) abs_x)) (curry into d))))
      (return d)))""")
  cdf = stats.norm(loc=0.0, scale=2.0).cdf
  result = out.asPandas()
  for k in ["x", "y", "iteration", "time (s)", "log score", "particle id", "(abs (sub y x))", "abs_x"]:
    assert k in result
    assert len(result[k]) == 30
  # Check that the dataset can be extracted again
  (result == out.asPandas()).all()
  # TODO Also check the distributions of x and the difference
  return reportKnownContinuous(cdf, result["y"], "N(0,1)")

def testPrintf():
  '''Intercept stdout and make sure the message read what we expect'''
  ripl = get_ripl()
  pattern = make_pattern()
  ripl.infer('(resample 2)')
  ripl.assume('x', 2.1)
  old_stdout = sys.stdout
  result = StringIO()
  sys.stdout = result
  ripl.infer('(repeat 2 (do (mh default one 1) (bind (collect x (labelled 3.1 foo)) printf)))')
  sys.stdout = old_stdout
  res = result.getvalue()
  assert pattern.match(res) is not None

def testPrintf2():
  '''Intercept stdout and make sure the message read what we expect'''
  ripl = get_ripl()
  pattern = make_pattern()
  ripl.infer('(resample 2)')
  ripl.assume('x', 2.1)
  old_stdout = sys.stdout
  result = StringIO()
  sys.stdout = result
  ripl.infer('(repeat 2 (do (mh default one 1) (printf (run (collect x (labelled 3.1 foo))))))')
  sys.stdout = old_stdout
  res = result.getvalue()
  assert pattern.match(res) is not None

def testCollectLogScore():
  '''In the presence of likelihood-free SP's, the calling "collect" or "printf"
  should not crash the program.'''
  class TestPSP(LikelihoodFreePSP):
    def simulate(self, args):
      x = args.operandValues[0]
      return x + stats.distributions.norm.rvs()
  tester = typed_nr(TestPSP(), [t.NumberType()], t.NumberType())
  ripl = get_ripl()
  ripl.bind_foreign_sp('test', tester)
  prog = '''
  [ASSUME x (test 0)]
  [ASSUME y (normal x 1)]
  [infer (collect x)]'''
  ripl.execute_program(prog)

def make_pattern():
  iteration = r".*x.*foo.*\n.*2.1.*3.1.*\n.*2.1.*3.1.*"
  return re.compile(iteration + iteration, re.DOTALL)

