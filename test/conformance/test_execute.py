import scipy.stats

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
[observe (normal x 1) 2]
[infer (mh default one %s)]""" % default_num_transitions_per_sample())
    predictions.append(ripl.sample("x"))
  cdf = scipy.stats.norm(loc=1, scale=2).cdf
  return reportKnownContinuous(cdf, predictions, "N(1, 2)")
