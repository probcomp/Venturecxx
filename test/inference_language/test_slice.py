# Copyright (c) 2014 MIT Probabilistic Computing Project.
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
from venture.test.stats import statisticalTest, reportKnownContinuous, reportKnownMeanVariance
from venture.test.config import get_ripl, collectSamples, default_num_transitions_per_sample, gen_on_inf_prim
from testconfig import config

@gen_on_inf_prim("slice")
def testAllSteppingOut():
  tests = (checkSliceBasic1, checkSliceNormalWithObserve1, checkSliceNormalWithObserve2a,
           checkSliceNormalWithObserve2b, checkSliceStudentT1, checkSliceStudentT2)
  for test in tests: yield test, 'slice'

@gen_on_inf_prim("slice_doubling")
def testAllDoubling():
  tests = (checkSliceBasic1, checkSliceNormalWithObserve1, checkSliceNormalWithObserve2a,
           checkSliceNormalWithObserve2b, checkSliceStudentT1, checkSliceStudentT2)
  for test in tests: yield test, 'slice_doubling'

def inferCommand(slice_method, transitions_mult):
  ntransitions = default_num_transitions_per_sample() * transitions_mult
  return "(%s default one 0.5 100 %s)" % (slice_method, ntransitions)

@statisticalTest
def checkSliceBasic1(slice_method):
  "Basic sanity test for slice"
  if (config["get_ripl"] != "lite") and (slice_method == 'slice_doubling'):
    raise SkipTest("Slice sampling with doubling only implemented in Lite.")
  ripl = get_ripl()
  ripl.assume("a", "(normal 10.0 1.0)",label="pid")
  predictions = collectSamples(ripl,"pid",infer=inferCommand(slice_method,1))
  cdf = stats.norm(loc=10, scale=1).cdf
  return reportKnownContinuous(cdf, predictions, "N(10,1.0))")

@statisticalTest
def checkSliceNormalWithObserve1(slice_method):
  "Checks the posterior distribution on a Gaussian given an unlikely observation"
  if (config["get_ripl"] != "lite") and (slice_method == 'slice_doubling'):
    raise SkipTest("Slice sampling with doubling only implemented in Lite.")
  ripl = get_ripl()
  ripl.assume("a", "(normal 10.0 1.0)",label="pid")
  ripl.observe("(normal a 1.0)", 14.0)
  # Posterior for a is normal with mean 12, precision 2
#  ripl.predict("(normal a 1.0)")

  predictions = collectSamples(ripl,"pid",infer=inferCommand(slice_method,1))
  cdf = stats.norm(loc=12, scale=math.sqrt(0.5)).cdf
  return reportKnownContinuous(cdf, predictions, "N(12,sqrt(0.5))")

@statisticalTest
def checkSliceNormalWithObserve2a(slice_method):
  "Checks the posterior distribution on a Gaussian given an unlikely observation.  The difference between this and 1 is an extra predict, which apparently has a deleterious effect on mixing."
  if (config["get_ripl"] != "lite") and (slice_method == 'slice_doubling'):
    raise SkipTest("Slice sampling with doubling only implemented in Lite.")
  ripl = get_ripl()
  ripl.assume("a", "(normal 10.0 1.0)", label="pid")
  ripl.observe("(normal a 1.0)", 14.0)
  # Posterior for a is normal with mean 12, precision 2
  ripl.predict("(normal a 1.0)")

  predictions = collectSamples(ripl,"pid",infer=inferCommand(slice_method,1))
  cdf = stats.norm(loc=12, scale=math.sqrt(0.5)).cdf
  return reportKnownContinuous(cdf, predictions, "N(12,sqrt(0.5))")

@statisticalTest
def checkSliceNormalWithObserve2b(slice_method):
  "Checks the posterior distribution on a Gaussian given an unlikely observation"
  if (config["get_ripl"] != "lite") and (slice_method == 'slice_doubling'):
    raise SkipTest("Slice sampling with doubling only implemented in Lite.")
  ripl = get_ripl()
  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.observe("(normal a 1.0)", 14.0)
  # Posterior for a is normal with mean 12, precision 2
  ripl.predict("(normal a 1.0)", label="pid")

  predictions = collectSamples(ripl,"pid",infer=inferCommand(slice_method,1))
  cdf = stats.norm(loc=12, scale=math.sqrt(1.5)).cdf
  return reportKnownContinuous(cdf, predictions, "N(12,sqrt(1.5))")

@statisticalTest
def checkSliceStudentT1(slice_method):
  "Simple program involving simulating from a student_t"
  if (config["get_ripl"] != "lite") and (slice_method == 'slice_doubling'):
    raise SkipTest("Slice sampling with doubling only implemented in Lite.")
  ripl = get_ripl()
  ripl.assume("a", "(student_t 1.0)", label="pid")
  ripl.observe("(normal a 1.0)", 3.0)
  predictions = collectSamples(ripl,"pid",infer=inferCommand(slice_method,1))

  # Posterior of a is proprtional to
  def postprop(a):
    return stats.t(1).pdf(a) * stats.norm(loc=3).pdf(a)
  import scipy.integrate as integrate
  (normalize,_) = integrate.quad(postprop, -10, 10)
  def posterior(a): return postprop(a) / normalize
  (meana,_) = integrate.quad(lambda x: x * posterior(x), -10, 10)
  (meanasq,_) = integrate.quad(lambda x: x * x * posterior(x), -10, 10)
  vara = meanasq - meana * meana
  return reportKnownMeanVariance(meana, vara, predictions)

@statisticalTest
def checkSliceStudentT2(slice_method):
  "Simple program involving simulating from a student_t"
  if (config["get_ripl"] != "lite") and (slice_method == 'slice_doubling'):
    raise SkipTest("Slice sampling with doubling only implemented in Lite.")
  ripl = get_ripl()
  ripl.assume("a", "(student_t 1.0)")
  ripl.observe("(normal a 1.0)", 3.0)
  ripl.predict("(normal a 1.0)", label="pid")
  predictions = collectSamples(ripl,"pid",infer=inferCommand(slice_method,4))

  # Posterior of a is proprtional to
  def postprop(a):
    return stats.t(1).pdf(a) * stats.norm(loc=3).pdf(a)
  import scipy.integrate as integrate
  (normalize,_) = integrate.quad(postprop, -10, 10)
  def posterior(a): return postprop(a) / normalize
  (meana,_) = integrate.quad(lambda x: x * posterior(x), -10, 10)
  (meanasq,_) = integrate.quad(lambda x: x * x * posterior(x), -10, 10)
  vara = meanasq - meana * meana
  return reportKnownMeanVariance(meana, vara + 1.0, predictions)
