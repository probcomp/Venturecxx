import scipy.stats as stats
import math
from venture.test.stats import statisticalTest, reportKnownDiscrete, reportKnownContinuous, reportKnownMeanVariance
from venture.test.config import get_ripl, collectSamples

def testEvalSmoke():
  for form in ["(get_current_environment)", "(get_empty_environment)",
               "(extend_environment (get_empty_environment) (quote foo) 5)"]:
    yield checkEvSmoke, form

def checkEvSmoke(form):
  get_ripl().predict(form)
  assert get_ripl().predict("(is_environment %s)" % form)

@statisticalTest
def testEval1():
  ripl = get_ripl()

  ripl.assume("globalEnv","(get_current_environment)")
  ripl.assume("expr","(quote (bernoulli 0.7))")
  ripl.predict("(eval expr globalEnv)")

  predictions = collectSamples(ripl,3)
  ans = [(1,.7), (0,.3)]
  return reportKnownDiscrete(ans, predictions)

@statisticalTest
def testEval2():
  ripl = get_ripl()

  ripl.assume("p","(uniform_continuous 0.0 1.0)")
  ripl.assume("globalEnv","(get_current_environment)")
  ripl.assume("expr","""
(quote
 (branch (bernoulli p)
   (quote (normal 10.0 1.0))
   (quote (normal 0.0 1.0))))
""")

  ripl.assume("x","(eval expr globalEnv)")
  ripl.observe("x",11.0)

  predictions = collectSamples(ripl,1)
  cdf = stats.beta(2,1).cdf # The observation nearly guarantees the first branch is taken
  return reportKnownContinuous(cdf, predictions, "approximately beta(2,1)")

@statisticalTest
def testEval3():
  "testEval2 with booby traps"
  ripl = get_ripl()

  ripl.assume("p","(uniform_continuous 0.0 1.0)")
  ripl.assume("globalEnv","(get_current_environment)")
  ripl.assume("expr","""
(quote
 (branch ((lambda () (bernoulli p)))
   (quote ((lambda () (normal 10.0 1.0))))
   (quote (normal 0.0 1.0))))
""")

  ripl.assume("x","(eval expr globalEnv)")
  ripl.observe("x",11.0)

  predictions = collectSamples(ripl,1)
  cdf = stats.beta(2,1).cdf # The observation nearly guarantees the first branch is taken
  return reportKnownContinuous(cdf, predictions, "approximately beta(2,1)")


@statisticalTest
def testApply1():
  "This CSP does not handle lists and symbols correctly."
  ripl = get_ripl()

  ripl.assume("apply","(lambda (op args) (eval (pair op args) (get_empty_environment)))")
  ripl.predict("(apply times (list (normal 10.0 1.0) (normal 10.0 1.0) (normal 10.0 1.0)))")

  predictions = collectSamples(ripl,2)
  return reportKnownMeanVariance(1000, 101**3 - 100**3, predictions)


# TODO not sure the best interface for extend_environment.
# Just like dict it could take a list of pairs.
# It could even take a dict!
@statisticalTest
def testExtendEnv1():
  ripl = get_ripl()

  ripl.assume("env1","(get_current_environment)")

  ripl.assume("env2","(extend_environment env1 (quote x) (normal 0.0 1.0))")
  ripl.assume("env3","(extend_environment env2 (quote x) (normal 10.0 1.0))")
  ripl.assume("expr","(quote (normal x 1.0))")
  ripl.predict("(normal (eval expr env3) 1.0)")

  predictions = collectSamples(ripl,5)
  cdf = stats.norm(loc=10, scale=math.sqrt(3)).cdf
  return reportKnownContinuous(cdf, predictions, "N(10,sqrt(3))")
