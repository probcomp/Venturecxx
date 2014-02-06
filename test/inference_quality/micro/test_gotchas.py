from venture.test.stats import statisticalTest, reportKnownDiscrete
from venture.test.config import get_ripl, collectSamples

def testInferWithNoEntropy():
  "Makes sure that infer doesn't crash when there are no random choices in the trace"
  ripl = get_ripl()
  ripl.infer(1)
  ripl.predict("(if true 1 2)")
  ripl.infer(1)
  
@statisticalTest
def testOuterMix1():
  "Makes sure that the mix-mh weights are correct"
  ripl = get_ripl()
  ripl.predict("(if (bernoulli 0.5) (if (bernoulli 0.5) 2 3) 1)")

  predictions = collectSamples(ripl,1)
  ans = [(1,.5), (2,.25), (3,.25)]
  return reportKnownDiscrete(ans, predictions)
