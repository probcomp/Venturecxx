from nose.tools import eq_, assert_raises # Pylint misses metaprogrammed names pylint:disable=no-name-in-module
from nose import SkipTest

from venture.test.stats import statisticalTest, reportKnownDiscrete
from venture.test.config import get_ripl, collectSamples, collectStateSequence, gen_broken_in, gen_on_inf_prim

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
  ripl.predict("(if (bernoulli 0.5) (if (bernoulli 0.5) 2 3) 1)", label="pid")

  predictions = collectSamples(ripl,"pid")
  ans = [(1,.5), (2,.25), (3,.25)]
  return reportKnownDiscrete(ans, predictions)

def progHiddenDeterminism():
  ripl = get_ripl()
  ripl.assume("c1", "(flip)", label="c1")
  ripl.assume("p",  "(if c1 1 0)")
  ripl.assume("c2", "(flip p)", label="c2") # c2 being different from c1 is impossible
  return ripl

# TODO Figure out a coherent way to run these two tests against all
# kernels including gibbs.  Should I rely on the "generic inference
# program" mechanism?
def testHiddenDeterminism1():
  """Makes sure that proposals of impossible things don't cause
  trouble"""
  ripl = progHiddenDeterminism()
  raise SkipTest("Crashes with a log(0) problem in log density of bernoulli.  Issue: https://app.asana.com/0/9277419963067/10386828313646")
  c1 = ripl.report("c1")
  # TODO Expand collectSamples to accept a list of indices and report all of them
  # TODO Expand collectSamples to accept the inference command as a string
  predictions = collectStateSequence(ripl, "c1", infer="(mh default one 20)")
  # Single-site MH can't move on this problem
  for pred in predictions:
    eq_(pred, c1)

def testHiddenDeterminism2():
  """Makes sure that blocking can avoid proposing impossible things."""
  ripl = progHiddenDeterminism()
  # TODO enumerative gibbs triggers the log(0) bug even when blocked.
  predictions = collectStateSequence(ripl, "c2", infer="(mh default all 50)")
  # Block MH should explore the posterior
  ans = [(True,.5), (False,.5)]
  return reportKnownDiscrete(ans, predictions)

@gen_broken_in('puma', "rejection is not implemented in Puma")
@gen_on_inf_prim("rejection")
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
        if not incl_mu and not incl_sigma and not incl_out: pass
        else: yield checkRejectNormal, incl_mu, incl_sigma, incl_out

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
  def doinfer():
    ripl.infer("(rejection scaffold 0 1)")
  if [incl_mu, incl_sigma, incl_out] == [True, True, False]:
    assert_raises(Exception, doinfer) # Can't do rejection on normal when mu and sigma are unknown
  else:
    doinfer()
