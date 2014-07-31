import scipy.stats as stats

from venture.test.stats import statisticalTest, reportKnownContinuous
from venture.test.config import get_ripl, default_num_samples, on_inf_prim

@statisticalTest
@on_inf_prim("peek") # Technically also MH, but not testing it
def testPeekSmoke1():
  ripl = get_ripl()
  ripl.assume("x", "(normal 0 1)")
  predictions = ripl.infer("(cycle ((mh default one 1) (peek x)) %s)" % default_num_samples())['x']
  cdf = stats.norm(loc=0.0, scale=1.0).cdf
  return reportKnownContinuous(cdf, predictions, "N(0,1)")

@statisticalTest
@on_inf_prim("peek")
def testPeekSmoke2():
  ripl = get_ripl()
  predictions = ripl.infer("(cycle ((peek (normal 0 1) x)) %s)" % default_num_samples())['x']
  cdf = stats.norm(loc=0.0, scale=1.0).cdf
  return reportKnownContinuous(cdf, predictions, "N(0,1)")

@statisticalTest
@on_inf_prim("peek_all") # Technically also resample and MH, but not testing them
def testPeekAllSmoke1():
  ripl = get_ripl()
  ripl.infer("(resample 2)")
  ripl.assume("x", "(normal 0 1)")
  predictionss = ripl.infer("(cycle ((mh default one 1) (peek_all x)) %s)" % default_num_samples())['x']
  for item in predictionss:
    assert len(item) == 2
  cdf = stats.norm(loc=0.0, scale=1.0).cdf
  return reportKnownContinuous(cdf, [i[0] for i in predictionss], "N(0,1)")

@statisticalTest
@on_inf_prim("peek_all") # Technically also resample, but not testing it
def testPeekAllSmoke2():
  ripl = get_ripl()
  ripl.infer("(resample 2)")
  predictionss = ripl.infer("(cycle ((peek_all (normal 0 1) x)) %s)" % default_num_samples())['x']
  for item in predictionss:
    assert len(item) == 2
  cdf = stats.norm(loc=0.0, scale=1.0).cdf
  return reportKnownContinuous(cdf, [i[0] for i in predictionss], "N(0,1)")

@statisticalTest
@on_inf_prim("plotf") # Technically also resample and MH, but not testing them
def testPlotfSmoke():
  # This is the example from examples/normal_plot.vnt
  ripl = get_ripl()
  ripl.infer("(resample 10)")
  ripl.assume("x", "(normal 0 1)")
  ripl.assume("y", "(normal x 1)")
  ripl.assume("abs", "(lambda (x) (if (< x 0) (- 0 x) x))")
  out = ripl.infer("(cycle ((mh default all 1) (plotf (ltsr lctl pc0r h0 h1 p0s2 p0d1ds) x y (abs (- y x)))) 3)")
  cdf = stats.norm(loc=0.0, scale=2.0).cdf
  result = out.dataset()
  for k in ["x", "y", "sweeps", "time (s)", "log score", "particle", "(abs (sub y x))"]:
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
