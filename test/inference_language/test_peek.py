import scipy.stats as stats
from nose.tools import eq_
import re
from StringIO import StringIO
import sys

from venture.test.stats import statisticalTest, reportKnownContinuous
from venture.test.config import get_ripl, default_num_samples, on_inf_prim

def extract_from_frame(infer_result, names):
  '''Extract trace for desired variable(s) from InferResult'''
  return infer_result.dataset()[names]

def extract_from_panel(infer_result, names):
  '''Extract trace for desired variable(s) from InferResult panel'''
  return infer_result.panel().loc[:,:,names]

@statisticalTest
@on_inf_prim("peek") # Technically also MH, but not testing it
def testPeekSmoke1():
  ripl = get_ripl()
  ripl.assume("x", "(normal 0 1)")
  predictions = extract_from_frame(ripl.infer("(cycle ((mh default one 1) (peek x)) %s)" % default_num_samples()), 'x')
  cdf = stats.norm(loc=0.0, scale=1.0).cdf
  return reportKnownContinuous(cdf, predictions, "N(0,1)")

@statisticalTest
@on_inf_prim("peek")
def testPeekSmoke2():
  ripl = get_ripl()
  predictions = extract_from_frame(ripl.infer("(cycle ((peek (normal 0 1))) %s)" % default_num_samples()), '(normal 0.0 1.0)')
  cdf = stats.norm(loc=0.0, scale=1.0).cdf
  return reportKnownContinuous(cdf, predictions, "N(0,1)")

def testPeekSmoke3():
  ripl = get_ripl()
  predictions = extract_from_frame(ripl.infer("(cycle ((peek (labelled (normal 0 1) label))) %s)" % default_num_samples()), 'label')
  cdf = stats.norm(loc=0.0, scale=1.0).cdf
  return reportKnownContinuous(cdf, predictions, "N(0,1)")

@statisticalTest
@on_inf_prim("peek") # Technically also resample and MH, but not testing them
def testPeekAllSmoke1():
  ripl = get_ripl()
  ripl.infer("(resample 2)")
  ripl.assume("x", "(normal 0 1)")
  predictionss = extract_from_panel(ripl.infer("(cycle ((mh default one 1) (peek x)) %s)" % default_num_samples()), 'x')
  eq_(predictionss.shape, (2,2))
  cdf = stats.norm(loc=0.0, scale=1.0).cdf
  return reportKnownContinuous(cdf, predictionss.values.ravel(), "N(0,1)")

@statisticalTest
@on_inf_prim("peek") # Technically also resample, but not testing it
def testPeekAllSmoke2():
  ripl = get_ripl()
  ripl.infer("(resample 2)")
  predictionss = extract_from_panel(ripl.infer("(cycle ((peek (labelled (normal 0 1) x))) %s)" % default_num_samples()), 'x')
  eq_(predictionss.shape, (2,2))
  cdf = stats.norm(loc=0.0, scale=1.0).cdf
  return reportKnownContinuous(cdf, predictionss.values.ravel(), "N(0,1)")

@statisticalTest
@on_inf_prim("plotf") # Technically also resample and MH, but not testing them
def testPlotfSmoke():
  # This is the example from examples/normal_plot.vnt
  ripl = get_ripl()
  ripl.infer("(resample 10)")
  ripl.assume("x", "(normal 0 1)")
  ripl.assume("y", "(normal x 1)")
  ripl.assume("abs", "(lambda (x) (if (< x 0) (- 0 x) x))")
  out = ripl.infer("(cycle ((mh default all 1) (plotf (ltsr lctl pc0r h0 h1 p0s2 p0d1ds) x y (abs (- y x)) (labelled (abs x) abs_x))) 3)")
  cdf = stats.norm(loc=0.0, scale=2.0).cdf
  result = out.dataset()
  for k in ["x", "y", "sweep count", "time (s)", "log score", "particle id", "(abs (sub y x))", "abs_x"]:
    assert k in result
    assert len(result[k]) == 30
  # Check that the dataset can be extracted again
  (result == out.dataset()).all()
  # TODO Also check the distributions of x and the difference
  return reportKnownContinuous(cdf, result["y"], "N(0,1)")

@on_inf_prim("plotf") # Technically also MH, but not testing it
def testPlotfDataset():
  # make sure that calling dataset multiple times works
  ripl = get_ripl()
  ripl.assume('x', '(normal 0 1)')
  out = ripl.infer('(cycle ((mh default one 1) (plotf h0 x)) 1)')
  ds = out.dataset()
  # using try-except make sure we get a failure instead of an error
  try:
    ds = out.dataset()
  except KeyError:
    assert False

def testPrintf():
  '''Intercept stdout and make sure the message read what we expect'''
  pattern = make_pattern()
  ripl = get_ripl()
  ripl.infer('(resample 2)')
  ripl.assume('x', 2.1)
  old_stdout = sys.stdout
  result = StringIO()
  sys.stdout = result
  ripl.infer('(cycle ((mh default one 1) (printf x score (labelled 3.1 foo) sweep time)) 2)')
  sys.stdout = old_stdout
  res = result.getvalue()
  assert pattern.match(res) is not None

def make_pattern():
  pattern = '''x: \[2.1, 2.1\]
Global log score: \[0, 0\]
foo: \[3.1, 3.1\]
Sweep count: 1
Wall time: .*\... s

x: \[2.1, 2.1\]
Global log score: \[0, 0\]
foo: \[3.1, 3.1\]
Sweep count: 2
Wall time: .*\... s

'''
  return re.compile(pattern)

