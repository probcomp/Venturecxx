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

from venture.test.stats import statisticalTest, reportKnownMean
from venture.test.config import get_ripl, collectSamples, skipWhenRejectionSampling, on_inf_prim
from nose import SkipTest
from testconfig import config

@on_inf_prim("none")
def testCMVNSmoke():
  if config["get_ripl"] != "lite": raise SkipTest("CMVN in lite only")  
  get_ripl().predict("((make_cmvn (array 1.0 1.0) 2 2 (matrix (array (array 1.0 0.0) (array 0.0 1.0)))))")

@statisticalTest  
def testCMVN2D_mu1():
  if config["get_ripl"] != "lite": raise SkipTest("CMVN in lite only")
  ripl = get_ripl()
  ripl.assume("m0","(array 5.0 5.0)")
  ripl.assume("k0","7.0")
  ripl.assume("v0","11.0")
  ripl.assume("S0","(matrix (array (array 13.0 0.0) (array 0.0 13.0)))")
  ripl.assume("f","(make_cmvn m0 k0 v0 S0)")

  ripl.predict("(f)",label="pid")

  predictions = collectSamples(ripl,"pid")

  mu1 = [p[0] for p in predictions]
  return reportKnownMean(5, mu1)

@statisticalTest  
def testCMVN2D_mu2():
  if config["get_ripl"] != "lite": raise SkipTest("CMVN in lite only")
  
  ripl = get_ripl()
  ripl.assume("m0","(array 5.0 5.0)")
  ripl.assume("k0","7.0")
  ripl.assume("v0","11.0")
  ripl.assume("S0","(matrix (array (array 13.0 0.0) (array 0.0 13.0)))")
  ripl.assume("f","(make_cmvn m0 k0 v0 S0)")

  ripl.predict("(f)",label="pid")

  predictions = collectSamples(ripl,"pid")

  mu2 = [p[1] for p in predictions]

  return reportKnownMean(5, mu2)

@skipWhenRejectionSampling("Cannot rejection sample cmvn AAA")
@statisticalTest  
def testCMVN2D_AAA():
  if config["get_ripl"] != "lite": raise SkipTest("CMVN in lite only")
  
  ripl = get_ripl()
  ripl.assume("m0","(array (normal 5.0 0.0001) (normal 5.0 0.0001))")
  ripl.assume("k0","7.0")
  ripl.assume("v0","11.0")
  ripl.assume("S0","(matrix (array (array 13.0 0.0) (array 0.0 13.0)))")
  ripl.assume("f","(make_cmvn m0 k0 v0 S0)")

  ripl.predict("(f)",label="pid")

  predictions = collectSamples(ripl,"pid")

  mu2 = [p[1] for p in predictions]

  return reportKnownMean(5, mu2)
  

  # Variance is not being tested
    
  # Sigma11 = float(sum([(p[0] - mu1) * (p[0] - mu1) for p in predictions]))/len(predictions)
  # Sigma12 = float(sum([(p[0] - mu1) * (p[1] - mu2) for p in predictions]))/len(predictions)
  # Sigma21 = float(sum([(p[1] - mu2) * (p[0] - mu1) for p in predictions]))/len(predictions)
  # Sigma22 = float(sum([(p[1] - mu2) * (p[1] - mu2) for p in predictions]))/len(predictions)

  # print "---TestMakeCMVN4---"
  # print "(1.81," + str(Sigma11) + ")"
  # print "(0," + str(Sigma12) + ")"
  # print "(0," + str(Sigma21) + ")"
  # print "(1.81," + str(Sigma22) + ")"
