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
from testconfig import config

from venture.test.config import collectSamples
from venture.test.config import default_num_samples
from venture.test.config import default_num_transitions_per_sample
from venture.test.config import gen_on_inf_prim
from venture.test.config import get_ripl
from venture.test.stats import reportKnownDiscrete
from venture.test.stats import reportKnownGaussian
from venture.test.stats import reportKnownMean
from venture.test.stats import statisticalTest

@gen_on_inf_prim("slice")
def testAllSteppingOut():
  tests = (checkSliceBasic1, checkSliceNormalWithObserve1,
           checkSliceNormalWithObserve2a, checkSliceNormalWithObserve2b,
           checkSliceStudentT1, checkSliceStudentT2, checkSliceL)
  for test in tests: yield test, 'slice'

@gen_on_inf_prim("slice_doubling")
def testAllDoubling():
  tests = (checkSliceBasic1, checkSliceNormalWithObserve1,
           checkSliceNormalWithObserve2a, checkSliceNormalWithObserve2b,
           checkSliceStudentT1, checkSliceStudentT2, checkSliceL)
  for test in tests: yield test, 'slice_doubling'

def inferCommand(slice_method):
  ntransitions = default_num_transitions_per_sample()
  return "(%s default one 0.5 10000 %s)" % (slice_method, ntransitions)

def myCollectSamples(ripl, method):
  return collectSamples(ripl,"pid",num_samples=default_num_samples(4),
                        infer=inferCommand(method))

@statisticalTest
def checkSliceBasic1(slice_method, seed):
  # Basic sanity test for slice
  if (config["get_ripl"] != "lite") and (slice_method == 'slice_doubling'):
    raise SkipTest("Slice sampling with doubling only implemented in Lite.")
  ripl = get_ripl(seed=seed)
  ripl.assume("a", "(normal 10.0 1.0)",label="pid")
  predictions = myCollectSamples(ripl, slice_method)
  return reportKnownGaussian(10, 1, predictions)

@statisticalTest
def checkSliceNormalWithObserve1(slice_method, seed):
  # Checks the posterior distribution on a Gaussian given an unlikely
  # observation
  if (config["get_ripl"] != "lite") and (slice_method == 'slice_doubling'):
    raise SkipTest("Slice sampling with doubling only implemented in Lite.")
  ripl = get_ripl(seed=seed)
  ripl.assume("a", "(normal 10.0 1.0)",label="pid")
  ripl.observe("(normal a 1.0)", 14.0)
  # Posterior for a is normal with mean 12, precision 2
#  ripl.predict("(normal a 1.0)")

  predictions = myCollectSamples(ripl, slice_method)
  return reportKnownGaussian(12, math.sqrt(0.5), predictions)

@statisticalTest
def checkSliceNormalWithObserve2a(slice_method, seed):
  # Checks the posterior distribution on a Gaussian given an unlikely
  # observation.  The difference between this and 1 is an extra
  # predict, which apparently has a deleterious effect on mixing.
  if (config["get_ripl"] != "lite") and (slice_method == 'slice_doubling'):
    raise SkipTest("Slice sampling with doubling only implemented in Lite.")
  ripl = get_ripl(seed=seed)
  ripl.assume("a", "(normal 10.0 1.0)", label="pid")
  ripl.observe("(normal a 1.0)", 14.0)
  # Posterior for a is normal with mean 12, precision 2
  ripl.predict("(normal a 1.0)")

  predictions = myCollectSamples(ripl, slice_method)
  return reportKnownGaussian(12, math.sqrt(0.5), predictions)

@statisticalTest
def checkSliceNormalWithObserve2b(slice_method, seed):
  # Checks the posterior distribution on a Gaussian given an unlikely
  # observation
  if (config["get_ripl"] != "lite") and (slice_method == 'slice_doubling'):
    raise SkipTest("Slice sampling with doubling only implemented in Lite.")
  ripl = get_ripl(seed=seed)
  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.observe("(normal a 1.0)", 14.0)
  # Posterior for a is normal with mean 12, precision 2
  ripl.predict("(normal a 1.0)", label="pid")

  predictions = myCollectSamples(ripl, slice_method)
  return reportKnownGaussian(12, math.sqrt(1.5), predictions)

@statisticalTest
def checkSliceStudentT1(slice_method, seed):
  # Simple program involving simulating from a student_t
  if (config["get_ripl"] != "lite") and (slice_method == 'slice_doubling'):
    raise SkipTest("Slice sampling with doubling only implemented in Lite.")
  ripl = get_ripl(seed=seed)
  ripl.assume("a", "(student_t 1.0)", label="pid")
  ripl.observe("(normal a 1.0)", 3.0)
  predictions = myCollectSamples(ripl, slice_method)

  # Posterior of a is proprtional to
  def postprop(a):
    return stats.t(1).pdf(a) * stats.norm(loc=3).pdf(a)
  import scipy.integrate as integrate
  (normalize,_) = integrate.quad(postprop, -10, 10)
  def posterior(a): return postprop(a) / normalize
  (meana,_) = integrate.quad(lambda x: x * posterior(x), -10, 10)
  (meanasq,_) = integrate.quad(lambda x: x * x * posterior(x), -10, 10)
  vara = meanasq - meana * meana
  # TODO Test agreement with the whole shape of the distribution, not
  # just the mean
  return reportKnownMean(meana, predictions, variance=vara)

@statisticalTest
def checkSliceStudentT2(slice_method, seed):
  # Simple program involving simulating from a student_t
  if (config["get_ripl"] != "lite") and (slice_method == 'slice_doubling'):
    raise SkipTest("Slice sampling with doubling only implemented in Lite.")
  ripl = get_ripl(seed=seed)
  ripl.assume("a", "(student_t 1.0)")
  ripl.observe("(normal a 1.0)", 3.0)
  ripl.predict("(normal a 1.0)", label="pid")
  predictions = myCollectSamples(ripl, slice_method)

  # Posterior of a is proprtional to
  def postprop(a):
    return stats.t(1).pdf(a) * stats.norm(loc=3).pdf(a)
  import scipy.integrate as integrate
  (normalize,_) = integrate.quad(postprop, -10, 10)
  def posterior(a): return postprop(a) / normalize
  (meana,_) = integrate.quad(lambda x: x * posterior(x), -10, 10)
  (meanasq,_) = integrate.quad(lambda x: x * x * posterior(x), -10, 10)
  vara = meanasq - meana * meana
  # TODO Test agreement with the whole shape of the distribution, not
  # just the mean
  return reportKnownMean(meana, predictions, variance=vara + 1.0)

@statisticalTest
def checkSliceL(slice_method, seed):
  # Checks slice sampling on an L-shaped distribution.
  if (config["get_ripl"] != "lite") and (slice_method == 'slice_doubling'):
    raise SkipTest("Slice sampling with doubling only implemented in Lite.")
  ripl = get_ripl(seed=seed)
  ripl.assume("a", "(uniform_continuous 0.0 1.0)")
  ripl.assume("b", "(< a 0.2)")
  ripl.observe("(flip (biplex b 0.8 0.2))", True)
  # Posterior for b is 0.5 true, 0.5 false
  ripl.predict("b", label="pid")

  predictions = myCollectSamples(ripl, slice_method)
  return reportKnownDiscrete([[True, 0.5], [False, 0.5]], predictions)
