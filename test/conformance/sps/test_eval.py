# Copyright (c) 2013, 2014 MIT Probabilistic Computing Project.
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
import math
from venture.test.stats import statisticalTest, reportKnownDiscrete
from venture.test.stats import reportKnownContinuous, reportKnownMean
from venture.test.stats import reportKnownGaussian
from venture.test.config import get_ripl, collectSamples, skipWhenRejectionSampling, on_inf_prim, gen_on_inf_prim
from nose import SkipTest
from nose.tools import eq_

@gen_on_inf_prim("none")
def testEnvSmoke():
  for form in ["(get_current_environment)", "(get_empty_environment)",
               "(extend_environment (get_empty_environment) (quote foo) 5)"]:
    yield checkEnvSmoke, form

def checkEnvSmoke(form):
  get_ripl().predict(form)
  assert get_ripl().predict("(is_environment %s)" % form)

@on_inf_prim("none")
def testEnvLookup():
  raise SkipTest("Should lookup work on environments?  They store nodes, not values.  Issue: https://app.asana.com/0/9277419963067/10249544822507")
  ripl = get_ripl()
  ripl.assume("e", "(extend_environment (get_empty_environment) (quote foo) 5)")
  eq_(ripl.predict("(lookup e (quote foo))"), 5.0)

@on_inf_prim("none")
def testEvalSmoke1():
  ripl = get_ripl()
  ripl.assume("e", "(extend_environment (get_empty_environment) (quote foo) 5)")
  eq_(ripl.predict("(eval (quote foo) e)"), 5.0)

@on_inf_prim("none")
def testEvalSmoke2():
  ripl = get_ripl()
  ripl.assume("x", "4")
  ripl.assume("e", "(get_current_environment)")
  eq_(ripl.predict("(eval (quote x) e)"), 4.0)

@on_inf_prim("none")
def testEvalSmoke3():
  "Eval should work on programmatically constructed expressions."
  ripl = get_ripl()
  ripl.assume("expr", "(array (quote add) 2 2)")
  eq_(ripl.predict("(eval expr (get_current_environment))"), 4.0)

@statisticalTest
def testEval1():
  ripl = get_ripl()

  ripl.assume("globalEnv","(get_current_environment)")
  ripl.assume("expr","(quote (bernoulli 0.7))")
  ripl.predict("(eval expr globalEnv)",label="pid")

  predictions = collectSamples(ripl,"pid")
  ans = [(1,.7), (0,.3)]
  return reportKnownDiscrete(ans, predictions)

@on_inf_prim("none")
def testEvalIf1():
  "Eval should work on expressions that require macro expansion"
  eq_(get_ripl().predict("(eval (quote (if true 1 2)) (get_current_environment))"), 1)

@on_inf_prim("none")
def testEvalIf2():
  "Eval should work on programmatically constructed expressions that require macro expansion"
  raise SkipTest("This fails because the stack's \"desugaring\" is not applied by eval itself to the expressions being evaluated.  Oops.  Issue: https://app.asana.com/0/9277419963067/10249544822511")
  ripl = get_ripl()
  ripl.assume("expr", "(array (quote if) true 1 2)")
  eq_(ripl.predict("(eval expr (get_current_environment))"), 1)

@skipWhenRejectionSampling("Rejection sampling doesn't work when resimulations of unknown code are observed")
@statisticalTest
def testEval2():
  ripl = get_ripl()

  ripl.assume("p","(uniform_continuous 0.0 1.0)",label="pid")
  ripl.assume("globalEnv","(get_current_environment)")
  ripl.assume("expr","""
(quote
 (branch (bernoulli p)
   (quote (normal 10.0 1.0))
   (quote (normal 0.0 1.0))))
""")

  ripl.assume("x","(eval expr globalEnv)")
  ripl.observe("x",11.0)

  predictions = collectSamples(ripl,"pid")
  cdf = stats.beta(2,1).cdf # The observation nearly guarantees the first branch is taken
  return reportKnownContinuous(cdf, predictions, "approximately beta(2,1)")

@skipWhenRejectionSampling("Rejection sampling doesn't work when resimulations of unknown code are observed")
@statisticalTest
def testEval3():
  "testEval2 with booby traps"
  ripl = get_ripl()

  ripl.assume("p","(uniform_continuous 0.0 1.0)",label="pid")
  ripl.assume("globalEnv","(get_current_environment)")
  ripl.assume("expr","""
(quote
 (branch ((lambda () (bernoulli p)))
   (quote ((lambda () (normal 10.0 1.0))))
   (quote (normal 0.0 1.0))))
""")

  ripl.assume("x","(eval expr globalEnv)")
  ripl.observe("x",11.0)

  predictions = collectSamples(ripl,"pid")
  cdf = stats.beta(2,1).cdf # The observation nearly guarantees the first branch is taken
  return reportKnownContinuous(cdf, predictions, "approximately beta(2,1)")


@statisticalTest
def testApply1():
  "This CSP does not handle lists and symbols correctly."
  ripl = get_ripl()

  ripl.assume("apply","(lambda (op args) (eval (pair op args) (get_empty_environment)))")
  ripl.predict("(apply mul (array (normal 10.0 1.0) (normal 10.0 1.0) (normal 10.0 1.0)))",
               label="pid")

  predictions = collectSamples(ripl,"pid")
  return reportKnownMean(1000, predictions, variance=101**3 - 100**3)


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
  ripl.predict("(normal (eval expr env3) 1.0)",label="pid")

  predictions = collectSamples(ripl,"pid")
  return reportKnownGaussian(10, math.sqrt(3), predictions)
