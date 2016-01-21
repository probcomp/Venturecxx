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

from nose.tools import eq_
from testconfig import config
import numpy as np
import scipy.stats

from venture.test.stats import statisticalTest, reportKnownContinuous
from venture.test.stats import reportKnownGaussian
from venture.test.config import get_ripl, collectSamples, on_inf_prim, inParallel, SkipTest

@on_inf_prim("none")
def testWishartSmoke():
  ripl = get_ripl()
  ripl.assume("s", "(id_matrix 5)")
  m1 = ripl.predict("(wishart s 5)")
  m2 = ripl.predict("(inv_wishart s 5)")
  eq_(m1.shape, (5, 5))
  eq_(m2.shape, (5, 5))
  assert np.all(m1 != 0)
  assert np.all(m2 != 0)

@statisticalTest
def testWishartPrior1():
  """Confirm that the diagonal elements of a Wishart are a chi-squared distribution."""

  if inParallel() and config["get_ripl"] == "puma":
    raise SkipTest("The Lite SPs in Puma interface is not thread-safe, and wishart comes from Lite.")

  ripl = get_ripl()
  ripl.assume("s", "(matrix (array (array 2 -1) (array -1 3)))")
  ripl.assume("m", "(wishart s 5)")
  ripl.predict("(lookup m (pair 0 0))", label="prediction")

  predictions = collectSamples(ripl, "prediction")
  cdf = scipy.stats.chi2(df=5, scale=2).cdf
  return reportKnownContinuous(cdf, predictions)

@statisticalTest
def testWishartPrior2():
  """Confirm that the diagonal elements of a Wishart are a chi-squared distribution."""

  if inParallel() and config["get_ripl"] == "puma":
    raise SkipTest("The Lite SPs in Puma interface is not thread-safe, and wishart comes from Lite.")

  ripl = get_ripl()
  ripl.assume("s", "(matrix (array (array 2 -1) (array -1 3)))")
  ripl.assume("m", "(wishart s 4.2)")
  ripl.predict("(lookup m (pair 1 1))", label="prediction")

  predictions = collectSamples(ripl, "prediction")
  cdf = scipy.stats.chi2(df=4.2, scale=3).cdf
  return reportKnownContinuous(cdf, predictions)

@statisticalTest
def testInvWishartPrior1():
  """Confirm that the diagonal elements of an inverse Wishart are an inverse Gamma distribution."""

  if inParallel() and config["get_ripl"] == "puma":
    raise SkipTest("The Lite SPs in Puma interface is not thread-safe, and wishart comes from Lite.")

  ripl = get_ripl()
  ripl.assume("s", "(matrix (array (array 2 -1) (array -1 3)))")
  ripl.assume("m", "(inv_wishart s 5)")
  ripl.predict("(lookup m (pair 0 0))", label="prediction")

  predictions = collectSamples(ripl, "prediction")
  cdf = scipy.stats.invgamma(a=2, scale=1).cdf
  return reportKnownContinuous(cdf, predictions)

@statisticalTest
def testInvWishartPrior2():
  """Confirm that the diagonal elements of an inverse Wishart are an inverse Gamma distribution."""

  if inParallel() and config["get_ripl"] == "puma":
    raise SkipTest("The Lite SPs in Puma interface is not thread-safe, and wishart comes from Lite.")

  ripl = get_ripl()
  ripl.assume("s", "(matrix (array (array 2 -1) (array -1 3)))")
  ripl.assume("m", "(inv_wishart s 4.2)")
  ripl.predict("(lookup m (pair 1 1))", label="prediction")

  predictions = collectSamples(ripl, "prediction")
  cdf = scipy.stats.invgamma(a=1.6, scale=1.5).cdf
  return reportKnownContinuous(cdf, predictions)

@statisticalTest
def testWishartPrior3():
  """Confirm that as dof increases, the elements of a Wishart obey the central limit theorem."""

  if inParallel() and config["get_ripl"] == "puma":
    raise SkipTest("The Lite SPs in Puma interface is not thread-safe, and wishart comes from Lite.")

  ripl = get_ripl()
  ripl.assume("s", "(id_matrix 3)")
  ripl.assume("m", "(wishart s 10000)")
  ripl.predict("(lookup m (pair 0 0))", label="prediction")

  predictions = collectSamples(ripl, "prediction")
  return reportKnownGaussian(10000, 141, predictions)

@statisticalTest
def testWishartPrior4():
  """Confirm that as dof increases, the elements of a Wishart obey the central limit theorem."""

  if inParallel() and config["get_ripl"] == "puma":
    raise SkipTest("The Lite SPs in Puma interface is not thread-safe, and wishart comes from Lite.")

  ripl = get_ripl()
  ripl.assume("s", "(id_matrix 3)")
  ripl.assume("m", "(wishart s 10000)")
  ripl.predict("(lookup m (pair 0 1))", label="prediction")

  predictions = collectSamples(ripl, "prediction")
  return reportKnownGaussian(0, 100, predictions)


@statisticalTest
def testInvWishartPrior3():
  """Confirm that as dof increases, the elements of a Wishart obey the central limit theorem."""

  if inParallel() and config["get_ripl"] == "puma":
    raise SkipTest("The Lite SPs in Puma interface is not thread-safe, and wishart comes from Lite.")

  ripl = get_ripl()
  ripl.assume("s", "(scale_matrix 10000 (id_matrix 3))")
  ripl.assume("m", "(inv_wishart s 10000)")
  ripl.predict("(lookup m (pair 0 0))", label="prediction")

  predictions = collectSamples(ripl, "prediction")
  return reportKnownGaussian(1, 0.0141, predictions)

@statisticalTest
def testInvWishartPrior4():
  """Confirm that as dof increases, the elements of a Wishart obey the central limit theorem."""

  if inParallel() and config["get_ripl"] == "puma":
    raise SkipTest("The Lite SPs in Puma interface is not thread-safe, and wishart comes from Lite.")

  ripl = get_ripl()
  ripl.assume("s", "(scale_matrix 10000 (id_matrix 3))")
  ripl.assume("m", "(inv_wishart s 10000)")
  ripl.predict("(lookup m (pair 0 1))", label="prediction")

  predictions = collectSamples(ripl, "prediction")
  return reportKnownGaussian(0, 0.01, predictions)
