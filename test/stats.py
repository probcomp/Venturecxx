import sys
import math
import itertools
import scipy.stats as stats
import numpy as np
from testconfig import config
import nose.tools as nose

def normalizeList(seq):
  denom = sum(seq)
  if denom > 0: return [ float(x)/denom for x in seq]
  else: return [0 for x in seq]

def countPredictions(predictions, seq):
  return [predictions.count(x) for x in seq]

def rmsDifference(eps,ops): return math.sqrt(sum([ math.pow(x - y,2) for (x,y) in zip(eps,ops)]))

def fmtlst(fmt, lst):
  return "[" + ", ".join(map((lambda n: fmt % n), lst)) + "]"

def tabulatelst(fmt, lst, width=10, prefix=""):
  structure = []
  rest = lst
  while len(rest) > width + 1: # Avoid length 1 widows
    structure.append(rest[:width])
    rest = rest[width:]
  structure.append(rest)
  substrs = [", ".join(map((lambda n: fmt % n), l)) for l in structure]
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

def reportKnownEqualDistributions(data): raise Exception("reportKnownEqualDistributions() not yet implemented")

# For a deterministic test that is nonetheless labeled statistical
def reportPassage(name):
  return TestResult("Passed %s" % name, 1.0, "")

def profile(N):
  import statprof # From sudo pip install statprof
  statprof.start()
  try:
    runAllTests(N)
  finally:
    statprof.stop()
    statprof.display()

def collectSamples(ripl,address,num_samples=None,infer=None):
  if num_samples is None:
    num_samples = int(config["num_samples"])
  if infer is None:
    infer = defaultInfer()
  elif infer == "mixes_slowly": # TODO Replace this awful hack with proper adjustment of tests for difficulty
    infer = defaultInfer()
    infer["transitions"] = 4 * int(infer["transitions"])

  predictions = []
  for _ in range(num_samples):
    # Going direct here saved 5 of 35 seconds on some unscientific
    # tests, presumably by avoiding the parser.
    ripl.sivm.core_sivm.engine.infer(infer)
    predictions.append(ripl.report(address))
    ripl.sivm.core_sivm.engine.reset()
  return predictions

def defaultInfer():
  numTransitionsPerSample = config["num_transitions_per_sample"]
  kernel = config["kernel"]
  scope = config["scope"]
  block = config["block"]
  return {"transitions":numTransitionsPerSample, "kernel":kernel, "scope":scope, "block":block}
