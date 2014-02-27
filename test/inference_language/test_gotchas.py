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

def testRejectNormal1():
  """Rejection sampling shouldn't work if both mean and variance of a
  normal are subject to change; shouldn't work if the mean is known
  but the variance and the output are unknown; but still should work
  if the mean and the output are known even if the variance is not
  (unless the mean and the output are exactly equal).

  TODO Actually, the logDensityBound of normal is well-defined as long
  as the variance is bounded away from zero, but that seems too hard
  to chase down."""
  for incl_mu in [False, True]:
    for incl_sigma in [False, True]:
      for incl_out in [False, True]:
        yield checkRejectNormal, incl_mu, incl_sigma, incl_out

def checkRejectNormal(incl_mu, incl_sigma, incl_out):
  # Sadly, there doesn't seem to be a pretty way to arrange the scopes
  # and blocks such that I can easily control all samples, except by
  # metaprogramming.
  def maybewrap(command, doit):
    if doit:
      return "(scope_include (quote scaffold) 0 %s)" % command
    else:
      return command
  ripl = get_ripl()
  ripl.assume("mu", maybewrap("(normal 0 1)", incl_mu))
  ripl.assume("sigma", maybewrap("(uniform_continuous 0 10)", incl_sigma))
  ripl.assume("out", maybewrap("(normal mu sigma)", incl_out))
  ripl.infer("(rejection scaffold 0 1)")
