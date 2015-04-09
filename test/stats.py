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
import scipy.stats as stats
import numpy as np
import nose.tools as nose
from testconfig import config
from venture.test.config import ignore_inference_quality
import sys

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
  """A container for a p-value and a report to print to the user if the test is deemed to have failed."""
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
  expRates = normalizeList([pair[1] for pair in expectedRates if pair[1] is not None])
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
    return stats.chisquare(cts1 + cts2, f_exp = np.array(expected1 + expected2), ddof = len(cts1 + cts2) - 1 - dof)

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
  ans = "Observed: % 4d samples with mean %4.3f, stddev %4.3f" % (count, mean, stddev)
  if count < 101:
    ans += ", data\n"
    ans += tabulatelst("%.2f", sorted(observed), width=10, prefix="  ")
  else:
    ans += ", percentiles\n"
    percentiles = [stats.scoreatpercentile(observed, p) for p in range(0,101)]
    ans += tabulatelst("%.2f", percentiles, width=10, prefix="  ")
  return ans

def reportKnownContinuous(expectedCDF, observed, descr=None):
  """Kolmogorov-Smirnov test for agreement with known 1-D cumulative density function.

  The CDF argument should be a Python callable that computes the cumulative density. """
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

# TODO Also sensibly compare the variance of the sample to the
# expected variance (what's the right test statistic when the
# "population distribution" is not known?  How many samples do I need
# for it to become effectively normal, if it does?)
# TODO Can I use the Barry-Esseen theorem to use skewness information
# for a more precise computation of test validity?  How about
# comparing sample skewness to expected skewness?
def reportKnownMeanVariance(expMean, expVar, observed):
  """Z-score test for data having a known mean and variance.

  Doesn't work for distributions that are fat-tailed enough not to
  have a mean.

  The K-S test done by reportKnownContinuous is much tighter, so try
  to use that if possible.

  """
  count = len(observed)
  mean = np.mean(observed)
  zscore = (mean - expMean) * math.sqrt(count) / math.sqrt(expVar)
  pval = 2*stats.norm.sf(abs(zscore)) # Two-tailed
  return TestResult(pval, "\n".join([
    "Expected: % 4d samples with mean %4.3f, stddev %4.3f" % (count, expMean, math.sqrt(expVar)),
    explainOneDSample(observed),
    "Z score : " + str(zscore),
    "P value : " + str(pval)]))

# TODO Warn if not enough observations?
def reportKnownMean(expMean, observed):
  """T-test for known mean, without knowing the variance.

  Doesn't work for distributions that are fat-tailed enough not to
  have a mean.

  The T-statistic is only valid if there are enough observations; 30
  are recommended.

  The K-S test done by reportKnownContinuous is much tighter, so try
  to use that if possible.
  """
  count = len(observed)
  (tstat, pval) = stats.ttest_1samp(observed, expMean)
  return TestResult(pval, "\n".join([
    "Expected: % 4d samples with mean %4.3f" % (count, expMean),
    explainOneDSample(observed),
    "T stat  : " + str(tstat),
    "P value : " + str(pval)]))

def reportPassage():
  """Pass a deterministic test that is nevertheless labeled statistical.

  Just returns a TestResult with p-value 1."""
  return TestResult(1.0, "")
