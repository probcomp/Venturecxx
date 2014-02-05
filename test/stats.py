import math
import scipy.stats as stats
import numpy as np
import nose.tools as nose
from testconfig import config

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
  def __init__(self, name, pval, report):
    self.name = name
    self.pval = pval
    self.report = report

  def __str__(self):
    return ("---Test: %s---\n" % self.name) + self.report

def fisherMethod(pvals):
  if any([p == 0 for p in pvals]):
    return 0
  else:
    chisq = -2 * sum([math.log(p) for p in pvals])
    return stats.chi2.sf(chisq, 2*len(pvals))

def repeatTest(func, *args):
  globalReportingThreshold = config["global_reporting_threshold"]
  result = func(*args)
  if config["ignore_inference_quality"]:
    return result
  if result.pval > 0.05:
    return result
  elif fisherMethod(result.pval + [1.0]*4) < globalReportingThreshold:
    return result
  else:
    print "Retrying suspicious test %s" % result.name
    results = [result] + [func(*args) for _ in range(1,5)]
    pval = fisherMethod([r.pval for r in results])
    report = "\n".join([r.report for r in results])
    report += "\nOverall P value: " + str(pval)
    return TestResult(result.name + " failing consistently", pval, report)

def reportTest(result):
  globalReportingThreshold = config["global_reporting_threshold"]
  if not config["ignore_inference_quality"]:
    assert result.pval > globalReportingThreshold, result

def statisticalTest(f):
  @nose.make_decorator(f)
  def wrapped(*args):
    reportTest(repeatTest(f, *args))
  return wrapped


# Chi^2 test for agreement with the given discrete distribution.
# TODO Broken (too stringent?) for small sample sizes; warn?
# reportKnownDiscrete :: (Eq a) => String -> [(a,Double)] -> [a] -> IO ()
def reportKnownDiscrete(name, expectedRates, observed):
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
  return TestResult(name, pval, "\n".join([
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

def reportSameDiscrete(name, observed1, observed2):
  items = sorted(set(observed1 + observed2))
  counts1 = [observed1.count(x) for x in items]
  counts2 = [observed2.count(x) for x in items]
  (chisq, pval) = chi2_contingency(counts1, counts2)
  return TestResult(name, pval, "\n".join([
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

# Kolmogorov-Smirnov test for agreement with known 1-D CDF.
def reportKnownContinuous(name, expectedCDF, observed, descr=None):
  (K, pval) = stats.kstest(observed, expectedCDF)
  return TestResult(name, pval, "\n".join([
    "Expected: %4d samples from %s" % (len(observed), descr),
    explainOneDSample(observed),
    "K stat  : " + str(K),
    "P value : " + str(pval)]))

def reportSameContinuous(name, observed1, observed2):
  (D, pval) = stats.ks_2samp(observed1, observed2)
  return TestResult(name, pval, "\n".join([
    "Expected samples from the same distribution",
    explainOneDSample(observed1),
    explainOneDSample(observed2),
    "D stat  : " + str(D),
    "P value : " + str(pval)]))

# Z-score test for known mean, given known variance.
# Doesn't work for distributions that are fat-tailed enough not to
# have a mean.
# TODO Also sensibly compare the variance of the sample to the
# expected variance (what's the right test statistic when the
# "population distribution" is not known?  How many samples do I need
# for it to become effectively normal, if it does?)
# TODO Can I use the Barry-Esseen theorem to use skewness information
# for a more precise computation of test validity?  How about
# comparing sample skewness to expected skewness?
def reportKnownMeanVariance(name, expMean, expVar, observed):
  count = len(observed)
  mean = np.mean(observed)
  zscore = (mean - expMean) * math.sqrt(count) / math.sqrt(expVar)
  pval = 2*stats.norm.sf(abs(zscore)) # Two-tailed
  return TestResult(name, pval, "\n".join([
    "Expected: % 4d samples with mean %4.3f, stddev %4.3f" % (count, expMean, math.sqrt(expVar)),
    explainOneDSample(observed),
    "Z score : " + str(zscore),
    "P value : " + str(pval)]))

# T-test for known mean, without knowing the variance.
# Doesn't work for distributions that are fat-tailed enough not to
# have a mean.
# TODO This is only valid if there are enough observations; 30 are recommended.
def reportKnownMean(name, expMean, observed):
  count = len(observed)
  (tstat, pval) = stats.ttest_1samp(observed, expMean)
  return TestResult(name, pval, "\n".join([
    "Expected: % 4d samples with mean %4.3f" % (count, expMean),
    explainOneDSample(observed),
    "T stat  : " + str(tstat),
    "P value : " + str(pval)]))

# For a deterministic test that is nonetheless labeled statistical
def reportPassage(name):
  return TestResult("Passed %s" % name, 1.0, "")
