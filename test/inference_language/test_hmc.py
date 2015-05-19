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
import scipy.stats as stats
from nose import SkipTest

from venture.test.stats import statisticalTest, reportKnownContinuous, reportSameContinuous
from venture.test.config import get_ripl, collectSamples, broken_in, gen_broken_in, on_inf_prim, gen_on_inf_prim
import venture.value.dicts as val

@broken_in('puma', "HMC only implemented in Lite.  Issue: https://app.asana.com/0/11192551635048/9277449877754")
@statisticalTest
@on_inf_prim("hmc")
def testNormalWithObserve1():
  "Checks the posterior distribution on a Gaussian given an unlikely observation"
  ripl = get_ripl()
  ripl.assume("a", "(normal 10.0 1.0)", label="pid")
  ripl.observe("(normal a 1.0)", 14.0)
  # Posterior for a is normal with mean 12, precision 2
#  ripl.predict("(normal a 1.0)")

  predictions = collectSamples(ripl,"pid",infer="(hmc default one 0.05 20 10)")
  cdf = stats.norm(loc=12, scale=math.sqrt(0.5)).cdf
  return reportKnownContinuous(cdf, predictions, "N(12,sqrt(0.5))")

@gen_on_inf_prim("mh")
def testMVGaussSmokeMH():
  yield checkMVGaussSmoke, "(mh default one 1)"

@gen_broken_in('puma', "HMC only implemented in Lite.  Issue: https://app.asana.com/0/11192551635048/9277449877754")
@gen_on_inf_prim("hmc")
def testMVGaussSmokeHMC():
  yield checkMVGaussSmoke, "(hmc default one 0.05 20 10)"

@statisticalTest
def checkMVGaussSmoke(infer):
  """Confirm that projecting a multivariate Gaussian to one dimension
  results in a univariate Gaussian."""
  ripl = get_ripl()
  ripl.assume("vec", "(multivariate_normal (vector 1 2) (matrix (list (list 1 0.5) (list 0.5 1))))")
  ripl.assume("x", "(lookup vec 0)", label="pid")
  predictions = collectSamples(ripl,"pid",infer=infer)
  cdf = stats.norm(loc=1, scale=1).cdf
  return reportKnownContinuous(cdf, predictions, "N(1,1)")

@gen_on_inf_prim("mh")
def testForceBrush1MH():
  yield checkForceBrush1, "(mh default one 2)"

@gen_broken_in('puma', "HMC only implemented in Lite.  Issue: https://app.asana.com/0/11192551635048/9277449877754")
@gen_on_inf_prim("hmc")
def testForceBrush1HMC():
  yield checkForceBrush1, "(hmc default one 0.05 20 10)"

@statisticalTest
def checkForceBrush1(infer):
  ripl = get_ripl()
  ripl.assume("x", "(normal 0 1)")
  ripl.predict("(if (< x 100) (normal x 1) (normal 100 1))", label="pid")
  predictions = collectSamples(ripl,"pid",infer=infer)
  cdf = stats.norm(loc=0, scale=math.sqrt(2)).cdf
  return reportKnownContinuous(cdf, predictions, "N(0,sqrt(2))")

@gen_on_inf_prim("mh")
def testForceBrush2MH():
  yield checkForceBrush2, "(mh default one 5)"

@gen_broken_in('puma', "HMC only implemented in Lite.  Issue: https://app.asana.com/0/11192551635048/9277449877754")
@gen_on_inf_prim("hmc")
def testForceBrush2HMC():
  yield checkForceBrush2, "(hmc default one 0.05 20 10)"

@statisticalTest
def checkForceBrush2(infer):
  ripl = get_ripl()
  ripl.assume("x", "(normal 0 1)")
  ripl.predict("(if (< x 0) (normal 0 1) (normal 100 1))", label="pid")
  predictions = collectSamples(ripl,"pid",infer=infer)
  cdf = lambda x: 0.5*stats.norm(loc=0, scale=1).cdf(x) + 0.5*stats.norm(loc=100, scale=1).cdf(x)
  return reportKnownContinuous(cdf, predictions, "N(0,1)/2 + N(100,1)/2")

@broken_in('puma', "HMC only implemented in Lite.  Issue: https://app.asana.com/0/11192551635048/9277449877754")
@statisticalTest
@on_inf_prim("hmc") # Really comparing MH and HMC
def testForceBrush3():
  ripl = get_ripl()
  ripl.assume("x", "(normal 0 1)")
  ripl.assume("y", "(if (< x 0) (normal x 1) (normal (+ x 10) 1))", label="pid")
  preds_mh = collectSamples(ripl, "pid", infer="(mh default one 10)")
  ripl.sivm.core_sivm.engine.reinit_inference_problem()
  preds_hmc = collectSamples(ripl, "pid", infer="(hmc default one 0.1 20 10)")
  return reportSameContinuous(preds_mh, preds_hmc)

@broken_in('puma', "HMC only implemented in Lite.  Issue: https://app.asana.com/0/11192551635048/9277449877754")
@statisticalTest
@on_inf_prim("hmc") # Really comparing MH and HMC
def testForceBrush4():
  ripl = get_ripl()
  ripl.assume("x", "(normal 0 1)")
  ripl.assume("y", "(if (< x 0) (normal x 1) (normal (+ x 10) 1))")
  ripl.predict("(normal y 1)", label="pid")
  preds_mh = collectSamples(ripl, "pid", infer="(mh default one 10)")
  ripl.sivm.core_sivm.engine.reinit_inference_problem()
  preds_hmc = collectSamples(ripl, "pid", infer="(hmc default one 0.1 20 10)")
  return reportSameContinuous(preds_mh, preds_hmc)

@broken_in('puma', "HMC only implemented in Lite.  Issue: https://app.asana.com/0/11192551635048/9277449877754")
@statisticalTest
@on_inf_prim("hmc") # Really comparing MH and HMC
def testForceBrush5():
  ripl = get_ripl()
  ripl.assume("x", "(normal 0 1)", label="pid")
  ripl.assume("y", "(if (< x 0) (normal x 1) (normal (+ x 10) 1))")
  ripl.observe("y", 8)
  preds_mh = collectSamples(ripl, "pid", infer="(mh default one 10)")
  ripl.sivm.core_sivm.engine.reinit_inference_problem()
  preds_hmc = collectSamples(ripl, "pid", infer="(hmc default one 0.1 20 10)")
  return reportSameContinuous(preds_mh, preds_hmc)

@broken_in('puma', "HMC only implemented in Lite.  Issue: https://app.asana.com/0/11192551635048/9277449877754")
@statisticalTest
@on_inf_prim("hmc") # Really comparing MH and HMC
def testMoreElaborate():
  """Confirm that HMC still works in the presence of brush.  Do not,
  however, mess with the possibility that the principal nodes that HMC
  operates over may themselves be in the brush."""
  ripl = get_ripl()
  ripl.assume("x", "(tag (quote param) 0 (uniform_continuous -10 10))")
  ripl.assume("y", "(tag (quote param) 1 (uniform_continuous -10 10))",
              label="pid")
  ripl.assume("xout", """
(if (< x 0)
    (normal x 1)
    (normal x 2))""")
  ripl.assume("out", "(multivariate_normal (array xout y) (matrix (list (list 1 0.5) (list 0.5 1))))")
  # Note: Can't observe coordinatewise because observe is not flexible
  # enough.  For this to work we would need observations of splits.
  # ripl.observe("(lookup out 0)", 0)
  # ripl.observe("(lookup out 1)", 0)
  # Can't observe through the ripl literally because the string
  # substitution (!) is not flexible enough.
  # ripl.observe("out", [0, 0])
  ripl.observe("out", val.list([val.real(0), val.real(0)]))

  preds_mh = collectSamples(ripl, "pid", infer="(mh default one 10)")
  ripl.sivm.core_sivm.engine.reinit_inference_problem()
  preds_hmc = collectSamples(ripl, "pid", infer="(hmc 'param all 0.1 20 10)")
  return reportSameContinuous(preds_mh, preds_hmc)

@broken_in('puma', "HMC only implemented in Lite.  Issue: https://app.asana.com/0/11192551635048/9277449877754")
@on_inf_prim("hmc") # Really comparing MH and HMC
def testMoveMatrix():
  ripl = get_ripl()
  ripl.assume("mu", "(array 0 0)")
  ripl.assume("scale", "(matrix (list (list 2 1) (list 1 2)))")
  ripl.assume("sigma", "(wishart scale 4)", label="pid")
  ripl.assume("out", "(multivariate_normal mu sigma)")
  ripl.observe("out", val.list([val.real(1), val.real(1)]))

  preds_mh = collectSamples(ripl, "pid", infer="(mh default one 30)")
  ripl.sivm.core_sivm.engine.reinit_inference_problem()
  preds_hmc = collectSamples(ripl, "pid", infer="(hmc default all 0.1 20 10)")
  # TODO Figure out either how to compare distributions on matrices,
  # or how to extract a real number whose distribution to compare.
  #   return reportSameContinuous(preds_mh, preds_hmc)

@broken_in('puma', "HMC only implemented in Lite.  Issue: https://app.asana.com/0/11192551635048/9277449877754")
@on_inf_prim("hmc")
def testTypeSmoke():
  raise SkipTest("Pending choice of representation of the zero gradient.  Issue: https://app.asana.com/0/11127829865276/15085515046349")
  ripl = get_ripl()
  ripl.assume("x", "(normal 0 1)")
  ripl.force("x", 2) # This two comes in as a VentureInteger!  Either
  # it should stay an integer and politely not move, or it should
  # become a VentureNumber and politely move, but it should not crash.
  ripl.infer("(hmc default one 0.1 10 1)")
