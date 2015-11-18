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

"""Support for statistical testing of Venture.

The general problem with testing random things is that they are
supposed to be random, so one never quite knows whether one got the
right behavior.

One can address this problem with statistical hypothesis testing: given
- a particular experimental setup (i.e., test case), and
- a particular measure of weirdness on observed results (i.e., test statistic),
- and the assumption that (the relevant portion of) Venture is correct,
one can compute a p-value for the observed results, and report a test
failure if that p-value is small enough to be noteworthy.

This module supplies facilities for testing in that style.  Of note:
- statisticalTest is an annotation that tags a test as being
  statistical in this way, and arranges for duly suspicious execution
- Every test annotated as a statisticalTest must return a
  TestResult object, which represents the p-value.
- The reportKnownFoo functions encapsulate standard statistical
  tests and return TestResult objects.
- This module respects the ignore_inference_quality configuration
  (which is on for the crash test suite and off for the inference
  quality test suite).

For example, here is one way to test a coin flipping device:

  from venture.test.stats import statisticalTest, reportKnownDiscrete

  @statisticalTest
  def test_flip_coins():
    observed = ... # Flip a bunch of coins and count the heads and tails
    expected = [("heads", 0.5), ("tails", 0.5)]
    return reportKnownDiscrete(expected, observed)

Note: When using the nose test generator feature, annotate the yielded
test function as @statisticalTest, not the generator.

"""

import math

import numpy as np
import nose.tools as nose
import sys
import scipy.stats as stats
from scipy.spatial.distance import pdist, squareform
from scipy.stats.mstats import rankdata

from testconfig import config
from venture.test.config import ignore_inference_quality

def normalizeList(seq):
  denom = sum(seq)
  if denom > 0: return [ float(x)/denom for x in seq]
  else: return [0 for x in seq]

def fmtlst(fmt, lst):
  return "[" + ", ".join([fmt % n for n in lst]) + "]"

def tabulatelst(fmt, lst, width=10, prefix=""):
  structure = []
  rest = lst
  while len(rest) > width + 1: # Avoid length 1 widows
    structure.append(rest[:width])
    rest = rest[width:]
  structure.append(rest)
  substrs = [", ".join([fmt % n for n in l]) for l in structure]
  bulk = (",\n" + prefix + " ").join(substrs)
  return prefix + "[" + bulk + "]"

class TestResult(object):
  """A container for a p-value and a report to print to the user if the test
  is deemed to have failed."""
  def __init__(self, pval, report):
    self.pval = pval
    self.report = report

  def __str__(self): return self.report

def fisherMethod(pvals):
  if any([p == 0 for p in pvals]):
    return 0
  else:
    chisq = -2 * sum([math.log(p) for p in pvals])
    return stats.chi2.sf(chisq, 2*len(pvals))

def repeatTest(func, *args):
  globalReportingThreshold = float(config["global_reporting_threshold"])
  result = func(*args)
  assert isinstance(result, TestResult)
  if ignore_inference_quality():
    return result
  if result.pval > 0.05:
    return result
  elif fisherMethod(result.pval + [1.0]*4) < globalReportingThreshold:
    # Hopeless
    return result
  else:
    print "Retrying suspicious test"
    def trial():
      answer = func(*args)
      sys.stdout.write(".")
      return answer
    results = [result] + [trial() for _ in range(1,5)]
    pval = fisherMethod([r.pval for r in results])
    report = "Test failing consistently\n"
    report += "\n".join([r.report for r in results])
    report += "\nOverall P value: " + str(pval)
    return TestResult(pval, report)

def reportTest(result):
  globalReportingThreshold = float(config["global_reporting_threshold"])
  if not ignore_inference_quality():
    assert result.pval > globalReportingThreshold, result

def statisticalTest(f):
  """Annotate a test function as being statistical.

  The function must return a TestResult (for example, using one of the
  reportKnownFoo functions), and must not object to being executed
  repeatedly.

  """
  @nose.make_decorator(f)
  def wrapped(*args):
    reportTest(repeatTest(f, *args))
  return wrapped


# TODO Broken (too stringent?) for small sample sizes; warn?
def reportKnownDiscrete(expectedRates, observed):
  """Chi^2 test for agreement with the given discrete distribution.
  reportKnownDiscrete :: (Eq a) => [(a,Double)] -> [a] -> TestResult

  The input format for the expected distribution is a list of
  item-rate pairs.  The probability of items that do not appear on the
  list is taken to be zero.  If a rate is given as None, that item is
  assumed possible but with unknown frequency.

  Try to have enough samples that every item is expected to appear at
  least five times for the Chi^2 statistic to be reasonable.

  """
  items = [pair[0] for pair in expectedRates]
  itemsDict = {pair[0]:pair[1] for pair in expectedRates}
  for o in observed:
    assert o in itemsDict, "Completely unexpected observation %r" % o
  # N.B. This is not None test allows observations to be selectively
  # ignored.  This is useful when information about the right answer
  # is incomplete.
  counts = [observed.count(x) for x in items if itemsDict[x] is not None]
  total = sum(counts)
  expRates = normalizeList([pair[1] for pair in expectedRates
    if pair[1] is not None])
  expCounts = [total * r for r in expRates]
  (chisq,pval) = stats.chisquare(counts, np.array(expCounts))
  return TestResult(pval, "\n".join([
    "Expected: " + fmtlst("% 4.1f", expCounts),
    "Observed: " + fmtlst("% 4d", counts),
    "Chi^2   : " + str(chisq),
    "P value : " + str(pval)]))

def chi2_contingency(cts1, cts2):
  if hasattr(stats, "chi2_contingency"):
    # Yes pylint, I am explicitly checking for the member
    # pylint: disable=no-member
    (chisq, pval, _, _) = stats.chi2_contingency([cts1, cts2])
    return (chisq, pval)
  else:
    # Reimplement it for the 2-dimensional 2xN case
    total = sum(cts1) + sum(cts2)
    ratio1 = float(sum(cts1))/total
    ratio2 = float(sum(cts2))/total
    expected1 = [ratio1 * (cts1[i] + cts2[i]) for i in range(len(cts1))]
    expected2 = [ratio2 * (cts1[i] + cts2[i]) for i in range(len(cts2))]
    assert len(expected1) == len(expected2)
    dof = len(expected1) -1
    return stats.chisquare(cts1 + cts2, f_exp=np.array(expected1 + expected2),
      ddof=len(cts1 + cts2) - 1 - dof)

def reportSameDiscrete(observed1, observed2):
  """Chi^2 test for sameness of two empirical discrete distributions.

  Try to have enough samples that every item is expected to appear at
  least five times for the Chi^2 statistic to be reasonable.

  """
  items = sorted(set(observed1 + observed2))
  counts1 = [observed1.count(x) for x in items]
  counts2 = [observed2.count(x) for x in items]
  (chisq, pval) = chi2_contingency(counts1, counts2)
  return TestResult(pval, "\n".join([
    "Expected two samples from the same discrete distribution",
    "Observed: " + fmtlst("% 4d", counts1),
    "Observed: " + fmtlst("% 4d", counts2),
    "Chi^2   : " + str(chisq),
    "P value : " + str(pval)]))

def explainOneDSample(observed):
  count = len(observed)
  mean = np.mean(observed)
  stddev = np.std(observed)
  ans = "Observed: % 4d samples with mean %4.3f, stddev %4.3f" \
    % (count, mean, stddev)
  if count < 101:
    ans += ", data\n"
    ans += tabulatelst("%.2f", sorted(observed), width=10, prefix="  ")
  else:
    ans += ", percentiles\n"
    percentiles = [stats.scoreatpercentile(observed, p) for p in range(0,101)]
    ans += tabulatelst("%.2f", percentiles, width=10, prefix="  ")
  return ans

def reportKnownContinuous(expectedCDF, observed, descr=None):
  """Kolmogorov-Smirnov test for agreement with known 1-D cumulative density
  function. The CDF argument should be a Python callable that computes the
  cumulative density."""
  (K, pval) = stats.kstest(observed, expectedCDF)
  return TestResult(pval, "\n".join([
    "Expected: %4d samples from %s" % (len(observed), descr),
    explainOneDSample(observed),
    "K stat  : " + str(K),
    "P value : " + str(pval)]))

def reportSameContinuous(observed1, observed2):
  """Kolmogorov-Smirnov test for sameness of two empirical 1-D continuous distributions."""
  (D, pval) = stats.ks_2samp(observed1, observed2)
  return TestResult(pval, "\n".join([
    "Expected samples from the same distribution",
    explainOneDSample(observed1),
    explainOneDSample(observed2),
    "D stat  : " + str(D),
    "P value : " + str(pval)]))

def reportKnownGaussian(expMean, expStdDev, observed):
  """Kolmogorov-Smirnov test for agreement with a known Gaussian.

  TODO Are there more sensitive tests for being a known Gaussian than
  K-S?
  """
  cdf = stats.norm(loc=expMean, scale=expStdDev).cdf
  return reportKnownContinuous(cdf, observed, "N(%s,%s)" % (expMean, expStdDev))

# TODO Warn if not enough observations?
def reportKnownMean(expMean, observed, variance=None):
  """Test for data having an expected mean.

  If the variance is not given, use a T-test.
  If the variance is given, use a (stricter) Z-score test.
  *Does not* test agreement of the observed variance.

  Doesn't work for distributions that are fat-tailed enough not to
  have a mean.

  The T-statistic is only a good approximation if there are enough
  observations; 30 are recommended.

  The K-S test done by reportKnownGaussian or reportKnownContinuous
  accounts for the entire shape of the distribution, so try to use
  that if possible.
  """
  if variance is not None:
    return reportKnownMeanZScore(expMean, variance, observed)
  count = len(observed)
  (tstat, pval) = stats.ttest_1samp(observed, expMean)
  return TestResult(pval, "\n".join([
    "Expected: % 4d samples with mean %4.3f" % (count, expMean),
    explainOneDSample(observed),
    "T stat  : " + str(tstat),
    "P value : " + str(pval)]))

def reportKnownMeanZScore(expMean, expVar, observed):
  """Z-score test for data having a known mean.

  Assumes the true variance is known and uses it to calibrate the mean
  test; *does not* test agreement with the observed variance.

  Doesn't work for distributions that are fat-tailed enough not to
  have a mean.

  The K-S test done by reportKnownContinuous accounts for the entire
  shape of the distribution, so try to use that if possible.

  If you know the distribution should be Gaussian, use
  reportKnownGaussian.
  """
  count = len(observed)
  mean = np.mean(observed)
  zscore = (mean - expMean) * math.sqrt(count) / math.sqrt(expVar)
  pval = 2*stats.norm.sf(abs(zscore)) # Two-tailed
  return TestResult(pval, "\n".join([
    "Expected: % 4d samples with mean %4.3f, stddev %4.3f" \
      % (count, expMean, math.sqrt(expVar)),
    explainOneDSample(observed),
    "Z score : " + str(zscore),
    "P value : " + str(pval)]))

# TODO Provide a test for distributions of unknown shape but known
# mean and variance that sensibly compares the variance of the sample
# to the expected variance.
# - What's the right test statistic when the "population distribution"
#   is not known?
# - How many samples do I need for the test statistic to become
#   effectively normal, if it does?
# - Can I use the Barry-Esseen theorem to use skewness information for
#   a more precise computation of test validity?  How about comparing
#   sample skewness to expected skewness?

def reportKernelTwoSampleTest(X, Y, permutations=None):
  '''
  Tests the null hypothesis that X and Y are samples drawn
  from the same population of arbitrary dimension D. The non-parametric
  permutation method is used and the test is exact. We use the statistic:
  E[k(X,X')] + E[k(Y,Y')] - 2E[k(X,Y)].

  A Gaussian kernel k(.,.) is used with width equal to the median distance
  between vectors in the aggregate sample. While the size of any permutation
  test is trivially exact, a permutation test with an arbitrary kernel is not
  guaranteed to have high power. However the Gaussian kernel has several
  optimal properties. For more information, see:

    http://www.stat.berkeley.edu/~sbalakri/Papers/MMD12.pdf

  :param X: List of N samples from the first population.
      Each entry in the list X must itself a D-dimensional (D>=1) list.
  :param Y: List of N samples from the second population.
      Each entry in the list Y must itself a D-dimensional (D>=1) list.
  :param permutations: (optional) number of times to resample, default 2500.

  :returns: p-value of the statistical test
  '''
  if permutations is None:
    permutations = 2500
  # Validate the inputs
  D = len(X[0])
  for x in X:
    assert len(x) == D
  for y in Y:
    assert len(y) == D
  X = np.asarray(X)
  Y = np.asarray(Y)
  assert isinstance(X, np.ndarray)
  assert isinstance(Y, np.ndarray)
  assert X.shape[1] == Y.shape[1]
  N = X.shape[0]

  # Compute the observed statistic.
  t_star = computeGaussianKernelStatistic(X, Y)
  T = [t_star]

  # Pool the samples.
  S = np.vstack((X, Y))

  # Compute resampled test statistics.
  for _ in xrange(permutations-1):
      np.random.shuffle(S)
      Xp, Yp = S[:N], S[N:]
      tb = computeGaussianKernelStatistic(Xp, Yp)
      T.append(tb)

  # Fraction of samples larger than observed t_star.
  t_star_rank = rankdata(T)[0]
  f = len(T) - t_star_rank
  pval = 1. * f / (len(T))

  return TestResult(pval, "\n".join([
    "Permutations        : %i" % permutations,
    "Observed Stat Rank  : %i" % t_star_rank,
    "P value             : %s" % str(pval)]))

def computeGaussianKernelStatistic(X, Y):
  """Compute a single two-sample test statistic using Gaussian kernel."""
  assert isinstance(X, np.ndarray)
  assert isinstance(Y, np.ndarray)
  assert X.shape[1] == Y.shape[1]

  N = X.shape[0]

  # Determine width of Gaussian kernel.
  Pxyxy = pdist(np.vstack((X, Y)), 'euclidean')
  s = np.median(Pxyxy)
  if s == 0:
      s = 1

  Kxy = squareform(Pxyxy)[:N, N:]
  Exy = np.exp(- Kxy ** 2 / s ** 2)
  Exy = np.mean(Exy)

  Kxx = squareform(pdist(X), 'euclidean')
  Exx = np.exp(- Kxx ** 2 / s ** 2)
  Exx = np.mean(Exx)

  Kyy = squareform(pdist(Y), 'euclidean')
  Eyy = np.exp(- Kyy ** 2 / s ** 2)
  Eyy = np.mean(Eyy)

  return Exx + Eyy - 2*Exy

def reportPassage():
  """Pass a deterministic test that is nevertheless labeled statistical.

  Just returns a TestResult with p-value 1."""
  return TestResult(1.0, "")
