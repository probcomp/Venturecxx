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

from nose.tools import assert_almost_equal
import scipy.stats as stats

from venture.test.config import collectSamples
from venture.test.config import default_num_samples
from venture.test.config import get_ripl
from venture.test.config import on_inf_prim
from venture.test.stats import reportKnownGaussian
from venture.test.stats import reportSameContinuous
from venture.test.stats import statisticalTest

@statisticalTest
@on_inf_prim("likelihood_weight")
def testNormalWithObserve1():
  # Checks the posterior distribution on a Gaussian given an unlikely
  # observation
  ripl = get_ripl()
  ripl.assume("a", "(normal 10.0 1.0)", label="pid")
  ripl.observe("(normal a 1.0)", 14.0)
  # Posterior for a is normal with mean 12, precision 2

  (samples, weights) = collectLikelihoodWeighted(ripl,"pid")
  for (s, w) in zip(samples, weights):
    # The weights I have should be deterministically given by the likelihood
    assert_almost_equal(math.exp(w), stats.norm(loc=14, scale=1).pdf(s))
  # The test points should be drawn from the prior
  return reportKnownGaussian(10, 1, samples)

def collectLikelihoodWeighted(ripl, address):
  vs = []
  wts = []
  for _ in range(default_num_samples()):
    ripl.infer("(likelihood_weight)")
    vs.append(ripl.report(address))
    wts.append(ripl.sivm.core_sivm.engine.model.log_weights[0])
  return (vs, wts)

@on_inf_prim("likelihood_weight")
def testMultiprocessingRegression():
  # Checking for a strange bug in likelihood_weight when using
  # parallel particles.
  #
  # The bug manifested as likelihood_weight producing a zero weight
  # for the distinguished particle every time.
  #
  # The problem actually was that the dump method of
  # engine.trace.Trace had the side-effect of unincorporating all
  # observations from the trace being dumped.  This would happen to
  # the distinguished trace at the beginning of every infer command,
  # because the Engine would request the distinguished trace in order
  # to perpetrate the self-evaluating scope hack.

  ripl = get_ripl()
  ripl.infer('(resample_multiprocess 2)')
  ripl.assume('x', '(normal 0 1)')
  ripl.observe('(normal x 1)', 5)
  ripl.infer('(likelihood_weight)')
  log_weights = ripl.sivm.core_sivm.engine.model.log_weights
  assert log_weights[0] != 0

@on_inf_prim("likelihood_weight")
def testRollingResample():
  ripl = get_ripl()
  ripl.assume("a", "(normal 10.0 1.0)", label="pid")
  ripl.observe("(normal a 1.0)", 14.0)

  flat_resample = "(do (resample 5) (likelihood_weight) (resample 1))"
  predictions1 = collectSamples(ripl, "pid", infer=flat_resample)

  rolling_resample = "(repeat 5 (do add_particle (resample 1)))"
  predictions2 = collectSamples(ripl, "pid", infer=rolling_resample)

  return reportSameContinuous(predictions1, predictions2)
