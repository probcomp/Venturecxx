# Copyright (c) 2013, MIT Probabilistic Computing Project.
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
# You should have received a copy of the GNU General Public License along with Venture.  If not, see <http://www.gnu.org/licenses/>.
from venture.shortcuts import *
import sys
import math
import pdb
import itertools
import scipy.stats as stats
import numpy as np

globalKernel = "mh";
globalUseGlobalScaffold = False;
globalAlwaysReport = False;
globalReportingThreshold = 0.001
globalBackend = make_lite_church_prime_ripl

def RIPL():
  return globalBackend()

def normalizeList(seq):
  denom = sum(seq)
  if denom > 0: return [ float(x)/denom for x in seq]
  else: return [0 for x in seq]

def countPredictions(predictions, seq):
  return [predictions.count(x) for x in seq]

def rmsDifference(eps,ops): return math.sqrt(sum([ math.pow(x - y,2) for (x,y) in zip(eps,ops)]))

def printTest(testName,eps,ops):
  print "---Test: " + testName + "---"
  print "Expected: " + str(eps)
  print "Observed: " + str(ops)
  print "Root Mean Square Difference: " + str(rmsDifference(eps,ops))

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
  result = func(*args)
  if result.pval > 0.05:
    return result
  elif fisherMethod(result.pval + [1.0]*4) < globalReportingThreshold:
    return result
  else:
    print "Retrying suspicious test %s" % result.name
    results = [result] + [func(*args) for i in range(1,5)]
    pval = fisherMethod([r.pval for r in results])
    report = "\n".join([r.report for r in results])
    report += "\nOverall P value: " + str(pval)
    return TestResult(result.name + " failing consistently", pval, report)

def reportTest(result):
  if globalAlwaysReport or result.pval < globalReportingThreshold:
    print result
  else:
    reportPassedQuitely()

def reportPassedQuitely():
  sys.stdout.write(".")
  sys.stdout.flush()

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

# For a deterministic test
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

def runAllTests(N):
  print "========= RunAllTests(N) ========"
  options = [ (make_church_prime_ripl, "mh", False),
              (make_church_prime_ripl, "mh", True),
              (make_church_prime_ripl, "pgibbs", False),
              (make_church_prime_ripl, "pgibbs", True),
              (make_church_prime_ripl, "meanfield", False),
              (make_church_prime_ripl, "meanfield", True),
              (make_church_prime_ripl, "gibbs", False),
              (make_lite_church_prime_ripl, "mh", False),
              (make_lite_church_prime_ripl, "meanfield", False)
              ]


  for i in range(len(options)):
    name = "CXX" if options[i][0] == make_church_prime_ripl else "Lite"
    print "\n========= %d. (%s, %s, %d) ========" % (i+1,name,options[i][1],options[i][2])
    global globalBackend
    global globalKernel
    global globalUseGlobalScaffold
    globalBackend = options[i][0]
    globalKernel = options[i][1]
    globalUseGlobalScaffold = options[i][2]
    runTests(N)

def collectSamples(ripl,address,T,kernel=None,use_global_scaffold=None):
  kernel = kernel if kernel is not None else globalKernel
  use_global_scaffold = use_global_scaffold if use_global_scaffold is not None else globalUseGlobalScaffold
  block = "one" if not use_global_scaffold else "all"
  return collectSamplesWith(ripl, address, T, {"transitions":100, "kernel":kernel, "block":block})

def collectSamplesWith(ripl, address, T, params):
  predictions = []
  for t in range(T):
    # Going direct here saved 5 of 35 seconds on some unscientific
    # tests, presumably by avoiding the parser.
    ripl.sivm.core_sivm.engine.infer(params)
    predictions.append(ripl.report(address))
    ripl.sivm.core_sivm.engine.reset()
  return predictions

def runTests(N):
  reportTest(testMakeCSP())
  reportTest(repeatTest(testBernoulli0, N))
  reportTest(repeatTest(testBernoulli1, N))
  reportTest(repeatTest(testCategorical1, N))
  reportTest(repeatTest(testMHNormal0, N))
  reportTest(repeatTest(testMHNormal1, N))
  runBlockingTests(N)
  reportTest(repeatTest(testMem0, N))
  reportTest(repeatTest(testMem1, N))
  reportTest(repeatTest(testMem2, N))
  reportTest(repeatTest(testMem3, N))
  reportTest(repeatTest(testSprinkler1, N))
  reportTest(repeatTest(testSprinkler2, N))
  reportTest(repeatTest(testIf1, N))
  reportTest(repeatTest(testIf2, N))
  reportTest(repeatTest(testBLOGCSI, N))
  reportTest(repeatTest(testMHHMM1, N))
  reportTest(repeatTest(testOuterMix1, N))
  reportTest(repeatTest(testMakeBetaBernoulli1, "make_beta_bernoulli", N))
  reportTest(repeatTest(testMakeBetaBernoulli2, "make_beta_bernoulli", N))
  reportTest(repeatTest(testMakeBetaBernoulli3, "make_beta_bernoulli", N))
  reportTest(repeatTest(testMakeBetaBernoulli4, "make_beta_bernoulli", N))
  if globalBackend == make_lite_church_prime_ripl:
    # These test primitives that only Lite has
    reportTest(repeatTest(testMakeBetaBernoulli1, "make_ubeta_bernoulli", N))
    reportTest(repeatTest(testMakeBetaBernoulli2, "make_ubeta_bernoulli", N))
    reportTest(repeatTest(testMakeBetaBernoulli3, "make_ubeta_bernoulli", N))
    reportTest(repeatTest(testMakeBetaBernoulli4, "make_ubeta_bernoulli", N))
  reportTest(repeatTest(testLazyHMM1, N))
  reportTest(repeatTest(testLazyHMMSP1, N))
  reportTest(repeatTest(testGamma1, N))
  reportTest(repeatTest(testBreakMem, N))
  if globalBackend != make_lite_church_prime_ripl:
    # These rely upon builtins primitives that the Lite backend doesn't have.
    # Those that are testing those primitives (as opposed to testing the engine with them)
    # can reasonably stay gated for a while.
    reportTest(repeatTest(testStudentT0, N))
    reportTest(repeatTest(testMakeSymDirMult1, "make_sym_dir_mult", N))
    reportTest(repeatTest(testMakeSymDirMult1, "make_uc_sym_dir_mult", N))
    reportTest(repeatTest(testMakeSymDirMult2, "make_sym_dir_mult", N))
    reportTest(repeatTest(testMakeSymDirMult2, "make_uc_sym_dir_mult", N))
    reportTest(repeatTest(testMakeDirMult1, N))
    reportTest(repeatTest(testStaleAAA1, N))
    reportTest(repeatTest(testStaleAAA2, N))
    reportTest(repeatTest(testMap1, N))
    reportTest(testMap2())
    reportTest(testMap3())
    reportTest(testMap4())
    reportTest(repeatTest(testEval1, N))
    reportTest(repeatTest(testEval2, N))
    reportTest(repeatTest(testEval3, N))
    reportTest(repeatTest(testApply1, N))
    reportTest(repeatTest(testExtendEnv1, N))
    reportTest(testList1())
    reportTest(repeatTest(testDPMem1, N))
    # reportTest(repeatTest(testCRP1, N, True)) # TODO Slow and fails too much
    # reportTest(repeatTest(testCRP1, N, False)) # Uncollapsed is too slow
    reportTest(repeatTest(testHPYMem1, N))
    reportTest(repeatTest(testGeometric1, N))
    reportTest(repeatTest(testTrig1, N))
    # Not missing a primitive, but Lite Traces cannot report their global log scores.
    reportTest(testForget1())
    reportTest(repeatTest(testReferences1, N))
    reportTest(repeatTest(testReferences2, N))
    # TODO This failure looks like a real bug
    reportTest(repeatTest(testMemoizingOnAList))
    # reportTest(repeatTest(testHPYLanguageModel1, N)) # TODO slow and fails
    # reportTest(repeatTest(testHPYLanguageModel2, N)) # TODO slow and fails
    reportTest(repeatTest(testGoldwater1, N))
  reportTest(repeatTest(testOperatorChanging, N))
  reportTest(repeatTest(testObserveAPredict0, N))
  # reportTest(repeatTest(testObserveAPredict1, N))
  # testObserveAPredict2(N)
  reportTest(testMemHashFunction1(5,5))

def runBlockingTests(N):
  if globalBackend == make_lite_church_prime_ripl:
    reportTest(repeatTest(testBlockingExample0, N))
    reportTest(testBlockingExample1())
    reportTest(testBlockingExample2())
    reportTest(testBlockingExample3())


def runTests2(N):
  reportTest(testGeometric1(N))



def testMakeCSP():
  ripl = RIPL()
  ripl.assume("f", "(lambda (x) (* x x))")
  ripl.predict("(f 1)")

  ripl.assume("g", "(lambda (x y) (* x y))")
  ripl.predict("(g 2 3)")

  ripl.assume("h", "(lambda () 5)")
  ripl.predict("(h)")

  assert(ripl.report(2) == 1.0)
  assert(ripl.report(4) == 6.0)
  assert(ripl.report(6) == 5.0)

  return reportPassage("TestMakeCSP")


def testBernoulli0(N):
  ripl = RIPL()
  ripl.assume("b", "((lambda () (bernoulli)))")
  ripl.predict("""
((biplex
  b
  (lambda () (normal 0.0 1.0))
  (lambda () ((lambda () (normal 10.0 1.0))))))
""");
  predictions = collectSamples(ripl,2,N)
  cdf = lambda x: 0.5 * stats.norm.cdf(x,loc=0,scale=1) + 0.5 * stats.norm.cdf(x,loc=10,scale=1)
  return reportKnownContinuous("TestBernoulli0", cdf, predictions, "N(0,1) + N(10,1)")

def testBernoulli1(N):
  ripl = RIPL()
  ripl.assume("b", "((lambda () (bernoulli 0.7)))")
  ripl.predict("""
(if b
  (normal 0.0 1.0)
  ((lambda () (normal 10.0 1.0))))
""");
  predictions = collectSamples(ripl,2,N)
  cdf = lambda x: 0.7 * stats.norm.cdf(x,loc=0,scale=1) + 0.3 * stats.norm.cdf(x,loc=10,scale=1)
  return reportKnownContinuous("TestBernoulli1", cdf, predictions, "0.7*N(0,1) + 0.3*N(10,1)")

def testCategorical1(N):
  ripl = RIPL()
  ripl.assume("x", "(real (categorical 0.1 0.2 0.3 0.4))")
  ripl.assume("y", "(real (categorical 0.2 0.6 0.2))")
  ripl.predict("(plus x y)")

  predictions = collectSamples(ripl,3,N)
  ans = [(0, 0.1 * 0.2),
         (1, 0.1 * 0.6 + 0.2 * 0.2),
         (2, 0.1 * 0.2 + 0.2 * 0.6 + 0.3 * 0.2),
         (3, 0.2 * 0.2 + 0.3 * 0.6 + 0.4 * 0.2),
         (4, 0.3 * 0.2 + 0.4 * 0.6),
         (5, 0.4 * 0.2)]
  return reportKnownDiscrete("testCategorical1", ans, predictions)

def testMHNormal0(N):
  ripl = RIPL()
  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.observe("(normal a 1.0)", 14.0)
  # Posterior for a is normal with mean 12, precision 2
  ripl.predict("(normal a 1.0)")

  predictions = collectSamples(ripl,3,N)
  cdf = stats.norm(loc=12, scale=math.sqrt(1.5)).cdf
  return reportKnownContinuous("testMHNormal0", cdf, predictions, "N(12,sqrt(1.5))")

def testMHNormal1(N):
  ripl = RIPL()
  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("b", "(normal a 1.0)")
  # Prior for b is normal with mean 10, variance 2 (precision 1/2)
  ripl.observe("((lambda () (normal b 1.0)))", 14.0)
  # Posterior for b is normal with mean 38/3, precision 3/2 (variance 2/3)
  # Likelihood of a is normal with mean 0, variance 2 (precision 1/2)
  # Posterior for a is normal with mean 34/3, precision 3/2 (variance 2/3)
  ripl.predict("""
(if (lt a 100.0)
  (normal (plus a b) 1.0)
  (normal (times a b) 1.0))
""")

  predictions = collectSamples(ripl,4,N)
  # Unfortunately, a and b are (anti?)correlated now, so the true
  # distribution of the sum is mysterious to me
  cdf = stats.norm(loc=24, scale=math.sqrt(7.0/3.0)).cdf
  return reportKnownContinuous("testMHNormal1", cdf, predictions, "approximately N(24,sqrt(7/3))")

def testBlockingExample0(N):
  ripl = RIPL()
  ripl.assume("a", "(scope_include 0 0 (normal 10.0 1.0))")
  ripl.assume("b", "(scope_include 1 1 (normal a 1.0))")
  ripl.observe("(normal b 1.0)", 14.0)

  # If inference only frobnicates b, then the distribution on a
  # remains the prior.
  predictions = collectSamplesWith(ripl,1,N,{"transitions":10,"kernel":globalKernel,"scope":1,"block":1})
  cdf = stats.norm(loc=10.0, scale=1.0).cdf
  return reportKnownContinuous("testBlockingExample0", cdf, predictions, "N(10.0,1.0)")

def testBlockingExample1():
  ripl = RIPL()
  ripl.assume("a", "(scope_include 0 0 (normal 0.0 1.0))")
  ripl.assume("b", "(scope_include 0 0 (normal 1.0 1.0))")
  olda = ripl.report(1)
  oldb = ripl.report(2)
  # The point of block proposals is that both things change at once.
  ripl.sivm.core_sivm.engine.infer({"transitions":1, "kernel":globalKernel, "scope":0, "block":0})
  newa = ripl.report(1)
  newb = ripl.report(2)
  assert not(olda == newa)
  assert not(oldb == newb)
  return reportPassage("testBlockingExample1")

def testBlockingExample2():
  ripl = RIPL()
  ripl.assume("a", "(scope_include 0 0 (normal 0.0 1.0))")
  ripl.assume("b", "(scope_include 0 0 (normal 1.0 1.0))")
  ripl.assume("c", "(scope_include 0 1 (normal 2.0 1.0))")
  ripl.assume("d", "(scope_include 0 1 (normal 3.0 1.0))")
  olda = ripl.report(1)
  oldb = ripl.report(2)
  oldc = ripl.report(3)
  oldd = ripl.report(4)
  # Should change everything in one or the other block
  ripl.sivm.core_sivm.engine.infer({"transitions":1, "kernel":globalKernel, "scope":0, "block":"one"})
  newa = ripl.report(1)
  newb = ripl.report(2)
  newc = ripl.report(3)
  newd = ripl.report(4)
  if (olda == newa):
    assert oldb == newb
    assert not(oldc == newc)
    assert not(oldd == newd)
  else:
    assert not(oldb == newb)
    assert oldc == newc
    assert oldd == newd
  return reportPassage("testBlockingExample2")

def testBlockingExample3():
  ripl = RIPL()
  ripl.assume("a", "(scope_include 0 0 (normal 0.0 1.0))")
  ripl.assume("b", "(scope_include 0 1 (normal 1.0 1.0))")
  olda = ripl.report(1)
  oldb = ripl.report(2)
  # The point of block proposals is that both things change at once.
  ripl.sivm.core_sivm.engine.infer({"transitions":1, "kernel":globalKernel, "scope":0, "block":"all"})
  newa = ripl.report(1)
  newb = ripl.report(2)
  assert not(olda == newa)
  assert not(oldb == newb)
  return reportPassage("testBlockingExample3")


def testStudentT0(N):
  ripl = RIPL()
  ripl.assume("a", "(student_t 1.0)")
  ripl.observe("(normal a 1.0)", 3.0)
  ripl.predict("(normal a 1.0)")
  predictions = collectSamples(ripl,3,N)

  # Posterior of a is proprtional to
  def postprop(a):
    return stats.t(1).pdf(a) * stats.norm(loc=3).pdf(a)
  import scipy.integrate as int
  (normalize,_) = int.quad(postprop, -10, 10)
  def posterior(a): return postprop(a) / normalize
  (meana,_) = int.quad(lambda x: x * posterior(x), -10, 10)
  (meanasq,_) = int.quad(lambda x: x * x * posterior(x), -10, 10)
  vara = meanasq - meana * meana
  return reportKnownMeanVariance("TestStudentT0", meana, vara + 1.0, predictions)

def testMem0(N):
  ripl = RIPL()
  ripl.assume("f","(mem (lambda (x) (bernoulli 0.5)))")
  ripl.predict("(f (bernoulli 0.5))")
  ripl.predict("(f (bernoulli 0.5))")
  ripl.infer(N, kernel="mh")
  return reportPassage("TestMem0")


def testMem1(N):
  ripl = RIPL()
  ripl.assume("f","(mem (lambda (arg) (plus 1 (real (categorical 0.4 0.6)))))")
  ripl.assume("x","(f 1)")
  ripl.assume("y","(f 1)")
  ripl.assume("w","(f 2)")
  ripl.assume("z","(f 2)")
  ripl.assume("q","(plus 1 (real (categorical 0.1 0.9)))")
  ripl.predict('(plus x y w z q)');

  predictions = collectSamples(ripl,7,N)
  # TODO This test can be strengthened by computing more of the ratios in the answer
  # (also by picking constants to have less severe buckets)
  ans = [(5,  0.4 * 0.4 * 0.1),
         (6,  None), (7,  None), (8,  None), (9,  None),
         (10, 0.6 * 0.6 * 0.9)]
  return reportKnownDiscrete("TestMem1", ans, predictions)

def testMem2(N):
  ripl = RIPL()
  ripl.assume("f","(mem (lambda (arg) (plus 1 (real (categorical 0.4 0.6)))))")
  ripl.assume("g","((lambda () (mem (lambda (y) (f (plus y 1))))))")
  ripl.assume("x","(f ((branch (bernoulli 0.5) (lambda () (lambda () 1)) (lambda () (lambda () 1)))))")
  ripl.assume("y","(g ((lambda () 0)))")
  ripl.assume("w","((lambda () (f 2)))")
  ripl.assume("z","(g 1)")
  ripl.assume("q","(plus 1 (real (categorical 0.1 0.9)))")
  ripl.predict('(plus x y w z q)');

  predictions = collectSamples(ripl,8,N)
  # TODO This test can be strengthened by computing more of the ratios in the answer
  # (also by picking constants to have less severe buckets)
  ans = [(5,  0.4 * 0.4 * 0.1),
         (6,  None), (7,  None), (8,  None), (9,  None),
         (10, 0.6 * 0.6 * 0.9)]
  return reportKnownDiscrete("TestMem2", ans, predictions)

def testMem3(N):
  ripl = RIPL()
  ripl.assume("f","(mem (lambda (arg) (plus 1 (real (categorical 0.4 0.6)))))")
  ripl.assume("g","((lambda () (mem (lambda (y) (f (plus y 1))))))")
  ripl.assume("x","(f ((lambda () 1)))")
  ripl.assume("y","(g ((lambda () (if (bernoulli 1.0) 0 100))))")
  ripl.assume("w","((lambda () (f 2)))")
  ripl.assume("z","(g 1)")
  ripl.assume("q","(plus 1 (real (categorical 0.1 0.9)))")
  ripl.predict('(plus x y w z q)');

  predictions = collectSamples(ripl,8,N)
  # TODO This test can be strengthened by computing more of the ratios in the answer
  # (also by picking constants to have less severe buckets)
  ans = [(5,  0.4 * 0.4 * 0.1),
         (6,  None), (7,  None), (8,  None), (9,  None),
         (10, 0.6 * 0.6 * 0.9)]
  return reportKnownDiscrete("TestMem3", ans, predictions)

def testSprinkler1(N):
  ripl = RIPL()
  ripl.assume("rain","(bernoulli 0.2)")
  ripl.assume("sprinkler","(if rain (bernoulli 0.01) (bernoulli 0.4))")
  ripl.assume("grassWet","""
(if rain
  (if sprinkler (bernoulli 0.99) (bernoulli 0.8))
  (if sprinkler (bernoulli 0.9)  (bernoulli 0.00001)))
""")
  ripl.observe("grassWet", True)

  predictions = collectSamples(ripl,1,N)
  ans = [(True, .3577), (False, .6433)]
  return reportKnownDiscrete("TestSprinkler1", ans, predictions)

def testSprinkler2(N):
  # this test needs more iterations than most others, because it mixes badly
  N = N

  ripl = RIPL()
  ripl.assume("rain","(bernoulli 0.2)")
  ripl.assume("sprinkler","(bernoulli (if rain 0.01 0.4))")
  ripl.assume("grassWet","""
(bernoulli
 (if rain
   (if sprinkler 0.99 0.8)
   (if sprinkler 0.9 0.00001)))
""")
  ripl.observe("grassWet", True)

  predictions = collectSamples(ripl,1,N)
  ans = [(True, .3577), (False, .6433)]
  return reportKnownDiscrete("TestSprinkler2 (mixes terribly)", ans, predictions)

def testGamma1(N):
  ripl = RIPL()
  ripl.assume("a","(gamma 10.0 10.0)")
  ripl.assume("b","(gamma 10.0 10.0)")
  ripl.predict("(gamma a b)")

  predictions = collectSamples(ripl,3,N)
  # TODO What, actually, is the mean of (gamma (gamma 10 10) (gamma 10 10))?
  # It's pretty clear that it's not 1.
  return reportKnownMean("TestGamma1", 10/9.0, predictions)

def testIf1(N):
  ripl = RIPL()
  ripl.assume('IF', '(lambda () branch)')
  ripl.assume('IF2', '(branch (bernoulli 0.5) IF IF)')
  ripl.predict('(IF2 (bernoulli 0.5) IF IF)')
  ripl.infer(N/10, kernel="mh")
  return reportPassage("TestIf1")

def testIf2(N):
  ripl = RIPL()
  ripl.assume('if1', '(branch (bernoulli 0.5) (lambda () branch) (lambda () branch))')
  ripl.assume('if2', '(branch (bernoulli 0.5) (lambda () if1) (lambda () if1))')
  ripl.assume('if3', '(branch (bernoulli 0.5) (lambda () if2) (lambda () if2))')
  ripl.assume('if4', '(branch (bernoulli 0.5) (lambda () if3) (lambda () if3))')
  ripl.infer(N/10, kernel="mh")
  return reportPassage("TestIf2")

def testBLOGCSI(N):
  ripl = RIPL()
  ripl.assume("u","(bernoulli 0.3)")
  ripl.assume("v","(bernoulli 0.9)")
  ripl.assume("w","(bernoulli 0.1)")
  ripl.assume("getParam","(lambda (z) (if z 0.8 0.2))")
  ripl.assume("x","(bernoulli (if u (getParam w) (getParam v)))")

  predictions = collectSamples(ripl,5,N)
  ans = [(True, .596), (False, .404)]
  return reportKnownDiscrete("TestBLOGCSI", ans, predictions)

def testMHHMM1(N):
  ripl = RIPL()
  ripl.assume("f","""
(mem (lambda (i)
  (if (eq i 0)
    (normal 0.0 1.0)
    (normal (f (minus i 1)) 1.0))))
""")
  ripl.assume("g","""
(mem (lambda (i)
  (normal (f i) 1.0)))
""")
  # Solution by forward algorithm inline
  # p((f 0))           = normal mean      0, var     1, prec 1
  # p((g 0) | (f 0))   = normal mean  (f 0), var     1, prec 1
  ripl.observe("(g 0)",1.0)
  # p((f 0) | history) = normal mean    1/2, var   1/2, prec 2
  # p((f 1) | history) = normal mean    1/2, var   3/2, prec 2/3
  # p((g 1) | (f 1))   = normal mean  (f 1), var     1, prec 1
  ripl.observe("(g 1)",2.0)
  # p((f 1) | history) = normal mean    7/5, var   3/5, prec 5/3
  # p((f 2) | history) = normal mean    7/5, var   8/5, prec 5/8
  # p((g 2) | (f 2))   = normal mean  (f 2), var     1, prec 1
  ripl.observe("(g 2)",3.0)
  # p((f 2) | history) = normal mean  31/13, var  8/13, prec 13/8
  # p((f 3) | history) = normal mean  31/13, var 21/13, prec 13/21
  # p((g 3) | (f 3))   = normal mean  (f 3), var     1, prec 1
  ripl.observe("(g 3)",4.0)
  # p((f 3) | history) = normal mean 115/34, var 21/34, prec 34/21
  # p((f 4) | history) = normal mean 115/34, var 55/34, prec 34/55
  # p((g 4) | (f 4))   = normal mean  (f 4), var     1, prec 1
  ripl.observe("(g 4)",5.0)
  # p((f 4) | history) = normal mean 390/89, var 55/89, prec 89/55
  ripl.predict("(f 4)")

  predictions = collectSamples(ripl,8,N)
  reportKnownMeanVariance("TestMHHMM1", 390/89.0, 55/89.0, predictions)
  cdf = stats.norm(loc=390/89.0, scale=math.sqrt(55/89.0)).cdf
  return reportKnownContinuous("TestMHHMM1", cdf, predictions, "N(4.382, 0.786)")

def testOuterMix1(N):
  ripl = RIPL()
  ripl.predict("(if (bernoulli 0.5) (if (bernoulli 0.5) 2 3) 1)")

  predictions = collectSamples(ripl,1,N)
  ans = [(1,.5), (2,.25), (3,.25)]
  return reportKnownDiscrete("TestOuterMix1", ans, predictions)

def testMakeSymDirMult1(name, N):
  ripl = RIPL()
  ripl.assume("f", "(%s 1.0 2)" % name)
  ripl.predict("(f)")
  predictions = collectSamples(ripl,2,N)
  ans = [(0,.5), (1,.5)]
  return reportKnownDiscrete("TestMakeSymDirMult1(%s)" % name, ans, predictions)

def testDirichletMultinomial1(name, ripl, index, N):
  for i in range(1,4):
    for j in range(20):
      ripl.observe("(f)", "atom<%d>" % i)

  predictions = collectSamples(ripl,index,N)
  ans = [(0,.1), (1,.3), (2,.3), (3,.3)]
  return reportKnownDiscrete("TestDirichletMultinomial(%s)" % name, ans, predictions)

def testMakeSymDirMult2(name, N):
  ripl = RIPL()
  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "(%s a 4)" % name)
  ripl.predict("(f)")
  return testDirichletMultinomial1(name, ripl, 3, N)

def testMakeDirMult1(N):
  ripl = RIPL()
  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "(make_dir_mult a a a a)")
  ripl.predict("(f)")
  return testDirichletMultinomial1("make_dir_mult", ripl, 3, N)

def testMakeBetaBernoulli1(maker, N):
  ripl = RIPL()
  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "(%s a a)" % maker)
  ripl.predict("(f)")

  for j in range(20): ripl.observe("(f)", "true")

  predictions = collectSamples(ripl,3,N)
  ans = [(False,.25), (True,.75)]
  return reportKnownDiscrete("TestMakeBetaBernoulli1 (%s)" % maker, ans, predictions)

# These three represent mechanisable ways of fuzzing a program for
# testing language feature interactions (in this case AAA with
# constraint forwarding and brush).
def testMakeBetaBernoulli2(maker, N):
  ripl = RIPL()
  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "((lambda () (%s ((lambda () a)) ((lambda () a)))))" % maker)
  ripl.predict("(f)")

  for j in range(20): ripl.observe("((lambda () (f)))", "true")

  predictions = collectSamples(ripl,3,N)
  ans = [(False,.25), (True,.75)]
  return reportKnownDiscrete("TestMakeBetaBernoulli2 (%s)" % maker, ans, predictions)

def testMakeBetaBernoulli3(maker, N):
  ripl = RIPL()
  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "(%s a a)" % maker)
  ripl.predict("(f)")

  for j in range(10): ripl.observe("(f)", "true")
  for j in range(10): ripl.observe("""
(if (lt a 10.0)
  (f)
  (f))""", "true")

  predictions = collectSamples(ripl,3,N)
  ans = [(False,.25), (True,.75)]
  return reportKnownDiscrete("TestMakeBetaBernoulli3 (%s)" % maker, ans, predictions)

def testMakeBetaBernoulli4(maker, N):
  ripl = RIPL()
  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", """
(if (lt a 10.0)
  ({0} a a)
  ({0} a a))""".format(maker))
  ripl.predict("(f)")

  for j in range(20): ripl.observe("(f)", "true")

  predictions = collectSamples(ripl,3,N)
  ans = [(False,.25), (True,.75)]
  return reportKnownDiscrete("TestMakeBetaBernoulli4 (%s)" % maker, ans, predictions)

def testLazyHMM1(N):
  N = N
  ripl = RIPL()
  ripl.assume("f","""
(mem (lambda (i)
  (if (eq i 0)
    (bernoulli 0.5)
    (if (f (minus i 1))
      (bernoulli 0.7)
      (bernoulli 0.3)))))
""")

  ripl.assume("g","""
(mem (lambda (i)
  (if (f i)
    (bernoulli 0.8)
    (bernoulli 0.1))))
""")

  ripl.observe("(g 1)",False)
  ripl.observe("(g 2)",False)
  ripl.observe("(g 3)",True)
  ripl.observe("(g 4)",False)
  ripl.observe("(g 5)",False)
  ripl.predict("(list (f 0) (f 1) (f 2) (f 3) (f 4) (f 5))")

  predictions = collectSamples(ripl,8,N)
  sums = [0 for i in range(6)]
  for p in predictions: sums = [sums[i] + p[i] for i in range(6)]
  ps = [.3531,.1327,.1796,.6925,.1796,.1327]
  eps = [float(x) / N for x in sums] if N > 0 else [0 for x in sums]
  printTest("testLazyHMM1 (mixes terribly)",ps,eps)
  return reportPassage("TestLazyHMM1")

def testLazyHMMSP1(N):
  ripl = RIPL()
  ripl.assume("f","""
(make_lazy_hmm
 (make_vector 0.5 0.5)
 (make_vector
  (make_vector 0.7 0.3)
  (make_vector 0.3 0.7))
 (make_vector
  (make_vector 0.9 0.2)
  (make_vector 0.1 0.8)))
""");
  ripl.observe("(f 1)","atom<0>")
  ripl.observe("(f 2)","atom<0>")
  ripl.observe("(f 3)","atom<1>")
  ripl.observe("(f 4)","atom<0>")
  ripl.observe("(f 5)","atom<0>")
  ripl.predict("(f 6)")
  ripl.predict("(f 7)")
  ripl.predict("(f 8)")

  predictions = collectSamples(ripl,7,N)
  ans = [(0,0.6528), (1,0.3472)]
  return reportKnownDiscrete("testLazyHMMSP1", ans, predictions)

def testStaleAAA1(N):
  ripl = RIPL()
  ripl.assume("a", "1.0")
  ripl.assume("f", "(make_uc_sym_dir_mult a 2)")
  ripl.assume("g", "(mem f)")
  ripl.assume("h", "g")
  ripl.predict("(h)")

  for i in range(9):
    ripl.observe("(f)", "atom<1>")

  predictions = collectSamples(ripl,5,N)
  ans = [(1,.9), (0,.1)]
  return reportKnownDiscrete("TestStaleAAA1", ans, predictions)

def testStaleAAA2(N):
  ripl = RIPL()
  ripl.assume("a", "1.0")
  ripl.assume("f", "(make_uc_sym_dir_mult a 2)")
  ripl.assume("g", "(lambda () f)")
  ripl.assume("h", "(g)")
  ripl.predict("(h)")

  for i in range(9):
    ripl.observe("(f)", "atom<1>")

  predictions = collectSamples(ripl,5,N)
  ans = [(1,.9), (0,.1)]
  return reportKnownDiscrete("TestStaleAAA2", ans, predictions)

def testMap1(N):
  ripl = RIPL()
  ripl.assume("x","(bernoulli 1.0)")
  ripl.assume("m","""(make_map (list (quote x) (quote y))
                               (list (normal 0.0 1.0) (normal 10.0 1.0)))""")
  ripl.predict("""(normal (plus
                           (map_lookup m (quote x))
                           (map_lookup m (quote y))
                           (map_lookup m (quote y)))
                         1.0)""")

  predictions = collectSamples(ripl,3,N)
  cdf = stats.norm(loc=20, scale=2).cdf
  return reportKnownContinuous("testMap1", cdf, predictions, "N(20,2)")

def testMap2():
  ripl = RIPL()
  ripl.assume("m","""(make_map (list (quote x) (quote y))
                               (list (normal 0.0 1.0) (normal 10.0 1.0)))""")
  ripl.predict("(map_contains m (quote x))",label="p1")
  ripl.predict("(map_contains m (quote y))",label="p2")
  ripl.predict("(map_contains m (quote z))",label="p3")

  assert ripl.report("p1")
  assert ripl.report("p2")
  assert not ripl.report("p3")
  return reportPassage("TestMap2")

def testMap3():
  ripl = RIPL()
  ripl.assume("m","""(make_map (list atom<1> atom<2>)
                               (list (normal 0.0 1.0) (normal 10.0 1.0)))""")
  ripl.predict("(map_contains m atom<1>)",label="p1")
  ripl.predict("(map_contains m atom<2>)",label="p2")
  ripl.predict("(map_contains m atom<3>)",label="p3")

  assert ripl.report("p1")
  assert ripl.report("p2")
  assert not ripl.report("p3")
  return reportPassage("TestMap3")

def testMap4():
  ripl = RIPL()
  ripl.assume("m","""(make_map (list (make_vector atom<1> atom<2>))
                               (list (normal 0.0 1.0)))""")
  ripl.predict("(map_contains m (make_vector atom<1> atom<2>))",label="p1")
  ripl.predict("(map_contains m atom<1>)",label="p2")
  ripl.predict("(map_contains m (make_vector atom<1>))",label="p3")

  assert ripl.report("p1")
  assert not ripl.report("p2")
  assert not ripl.report("p3")
  return reportPassage("TestMap4")

def testEval1(N):
  ripl = RIPL()
  ripl.assume("globalEnv","(get_current_environment)")
  ripl.assume("exp","(quote (bernoulli 0.7))")
  ripl.predict("(eval exp globalEnv)")

  predictions = collectSamples(ripl,3,N)
  ans = [(1,.7), (0,.3)]
  return reportKnownDiscrete("TestEval1", ans, predictions)

def testEval2(N):
  ripl = RIPL()
  ripl.assume("p","(uniform_continuous 0.0 1.0)")
  ripl.assume("globalEnv","(get_current_environment)")
  ripl.assume("exp","""
(quote
 (branch (bernoulli p)
   (lambda () (normal 10.0 1.0))
   (lambda () (normal 0.0 1.0)))
)""")

  ripl.assume("x","(eval exp globalEnv)")
  ripl.observe("x",11.0)

  predictions = collectSamples(ripl,1,N)
  cdf = stats.beta(2,1).cdf # The observation nearly guarantees the first branch is taken
  return reportKnownContinuous("testEval2", cdf, predictions, "approximately beta(2,1)")

def testEval3(N):
  ripl = RIPL()
  ripl.assume("p","(uniform_continuous 0.0 1.0)")
  ripl.assume("globalEnv","(get_current_environment)")
  ripl.assume("exp","""
(quote
 (branch ((lambda () (bernoulli p)))
   (lambda () ((lambda () (normal 10.0 1.0))))
   (lambda () (normal 0.0 1.0)))
)""")

  ripl.assume("x","(eval exp globalEnv)")
  ripl.observe("x",11.0)

  predictions = collectSamples(ripl,1,N)
  cdf = stats.beta(2,1).cdf # The observation nearly guarantees the first branch is taken
  return reportKnownContinuous("testEval3", cdf, predictions, "approximately beta(2,1)")

def testApply1(N):
  ripl = RIPL()
  ripl.assume("apply","(lambda (op args) (eval (pair op args) (get_empty_environment)))")
  ripl.predict("(apply times (list (normal 10.0 1.0) (normal 10.0 1.0) (normal 10.0 1.0)))")

  predictions = collectSamples(ripl,2,N)
  return reportKnownMeanVariance("TestApply1", 1000, 101**3 - 100**3, predictions)

def testExtendEnv1(N):
  ripl = RIPL()
  ripl.assume("env1","(get_current_environment)")

  ripl.assume("env2","(extend_environment env1 (quote x) (normal 0.0 1.0))")
  ripl.assume("env3","(extend_environment env2 (quote x) (normal 10.0 1.0))")
  ripl.assume("exp","(quote (normal x 1.0))")
  ripl.predict("(normal (eval exp env3) 1.0)")

  predictions = collectSamples(ripl,5,N)
  cdf = stats.norm(loc=10, scale=math.sqrt(3)).cdf
  return reportKnownContinuous("testExtendEnv1", cdf, predictions, "N(10,sqrt(3))")

# TODO need extend_env, symbol?
def riplWithSTDLIB(ripl):
  ripl.assume("make_ref","(lambda (x) (lambda () x))")
  ripl.assume("deref","(lambda (x) (x))")
  ripl.assume("venture_apply","(lambda (op args) (eval (pair op args) (get_empty_environment)))")
  ripl.assume("incremental_apply","""
(lambda (operator operands)
  (incremental_eval (deref (list_ref operator 3))

                    (extend_env env
				(deref (list_ref operator 2))
                                operands)))
""")
  ripl.assume("incremental_eval","""
(lambda (exp env)
  (branch
    (is_symbol exp)
    (quote (eval exp env))
    (quote
      (branch
        (not (is_pair exp))
        (quote exp)
        (branch
          (sym_eq (deref (list_ref exp 0)) (quote lambda))
	  (quote (pair env (rest exp)))
          (quote
            ((lambda (operator operands)
               (branch
                 (is_pair operator)
                 (quote (incremental_apply operator operands))
                 (quote (venture_apply operator operands))))
             (incremental_eval (deref (first exp)) env)
             (map_list (lambda (x) (make_ref (incremental_eval (deref x) env))) (rest exp))))
)))))
""")
  return ripl

def testList1():
  ripl = RIPL()
  ripl.assume("x1","(list)")
  ripl.assume("x2","(pair 1.0 x1)")
  ripl.assume("x3","(pair 2.0 x2)")
  ripl.assume("x4","(pair 3.0 x3)")
  ripl.assume("f","(lambda (x) (times x x x))")
  ripl.assume("y4","(map_list f x4)")

  y4 = ripl.predict("(first y4)")
  y3 = ripl.predict("(list_ref y4 1)")
  y2 = ripl.predict("(list_ref (rest y4) 1)")
  px1 = ripl.predict("(is_pair x1)")
  px4 = ripl.predict("(is_pair x4)")
  py4 = ripl.predict("(is_pair y4)")

  assert(ripl.report(7) == 27.0);
  assert(ripl.report(8) == 8.0);
  assert(ripl.report(9) == 1.0);

  assert(not ripl.report(10));
  assert(ripl.report(11));
  assert(ripl.report(11));

  return reportPassage("TestList1")

def loadPYMem(ripl):
  ripl.assume("pick_a_stick","""
(lambda (sticks k)
  (branch (bernoulli (sticks k))
    (lambda () k)
    (lambda () (pick_a_stick sticks (plus k 1)))))
""")

  ripl.assume("make_sticks","""
(lambda (alpha d)
  ((lambda (sticks) (lambda () (pick_a_stick sticks 1)))
   (mem (lambda (k)
     (beta (minus 1 d)
           (plus alpha (times k d)))))))
""")

  ripl.assume("u_pymem","""
(lambda (alpha d base_dist)
  ((lambda (augmented_proc py)
     (lambda () (augmented_proc (py))))
   (mem (lambda (stick_index) (base_dist)))
   (make_sticks alpha d)))
""")

  ripl.assume("pymem","""
(lambda (alpha d base_dist)
  ((lambda (augmented_proc crp)
     (lambda () (augmented_proc (crp))))
   (mem (lambda (table) (base_dist)))
   (make_crp alpha d)))
""")

def loadDPMem(ripl):
  ripl.assume("pick_a_stick","""
(lambda (sticks k)
  (branch (bernoulli (sticks k))
    (quote k)
    (quote (pick_a_stick sticks (plus k 1)))))
""")

  ripl.assume("make_sticks","""
(lambda (alpha)
  ((lambda (sticks) (lambda () (pick_a_stick sticks 1)))
   (mem (lambda (k)
     (beta 1 alpha)))))
""")

  ripl.assume("u_dpmem","""
(lambda (alpha base_dist)
  ((lambda (augmented_proc py)
     (lambda () (augmented_proc (py))))
   (mem (lambda (stick_index) (base_dist)))
   (make_sticks alpha)))
""")


def testDPMem1(N):
  ripl = RIPL()
  loadDPMem(ripl)

  ripl.assume("alpha","(uniform_continuous 0.1 20.0)")
  ripl.assume("base_dist","(lambda () (real (categorical 0.5 0.5)))")
  ripl.assume("f","(u_dpmem alpha base_dist)")

  ripl.predict("(f)")
  ripl.predict("(f)")
  ripl.observe("(normal (f) 1.0)",1.0)
  ripl.observe("(normal (f) 1.0)",1.0)
  ripl.observe("(normal (f) 1.0)",0.0)
  ripl.observe("(normal (f) 1.0)",0.0)
  ripl.infer(N)
  return reportPassage("TestDPMem1")

def observeCategories(ripl,counts):
  for i in range(len(counts)):
    for ct in range(counts[i]):
      ripl.observe("(flip (if (= (f) %d) 1.0 0.1))" % i,"true")

def testCRP1(N,isCollapsed):
  ripl = RIPL()
  loadPYMem(ripl)
  ripl.assume("alpha","(gamma 1.0 1.0)")
  ripl.assume("d","(uniform_continuous 0.0 0.1)")
  ripl.assume("base_dist","(lambda () (real (categorical 0.2 0.2 0.2 0.2 0.2)))")
  if isCollapsed: ripl.assume("f","(pymem alpha d base_dist)")
  else: ripl.assume("f","(u_pymem alpha d base_dist)")

  ripl.predict("(f)",label="pid")

  observeCategories(ripl,[2,2,5,1,0])

  predictions = collectSamples(ripl,"pid",N)
  ans = [(0,3), (1,3), (2,6), (3,2), (4,1)]
  return reportKnownDiscrete("TestCRP1 (not exact)", ans, predictions)

def loadHPY(ripl,topCollapsed,botCollapsed):
  loadPYMem(ripl)
  ripl.assume("alpha","(gamma 1.0 1.0)")
  ripl.assume("d","(uniform_continuous 0.0 0.1)")
  ripl.assume("base_dist","(lambda () (real (categorical 0.2 0.2 0.2 0.2 0.2)))")
  if topCollapsed: ripl.assume("intermediate_dist","(pymem alpha d base_dist)")
  else: ripl.assume("intermediate_dist","(u_pymem alpha d base_dist)")
  if botCollapsed: ripl.assume("f","(pymem alpha d intermediate_dist)")
  else: ripl.assume("f","(u_pymem alpha d intermediate_dist)")

def loadPY(ripl):
  loadPYMem(ripl)
  ripl.assume("alpha","(gamma 1.0 1.0)")
  ripl.assume("d","(uniform_continuous 0 0.0001)")
  ripl.assume("base_dist","(lambda () (real (categorical 0.2 0.2 0.2 0.2 0.2)))")
  ripl.assume("f","(u_pymem alpha d base_dist)")

def predictPY(N):
  ripl = RIPL()
  loadPY(ripl)
  ripl.predict("(f)",label="pid")
  observeCategories(ripl,[2,2,5,1,0])
  return collectSamples(ripl,"pid",N)

def predictHPY(N,topCollapsed,botCollapsed):
  ripl = RIPL()
  loadHPY(ripl,topCollapsed,botCollapsed)
  ripl.predict("(f)",label="pid")
  observeCategories(ripl,[2,2,5,1,0])
  return collectSamples(ripl,"pid",N)

def doTestHPYMem1(N):
  data = [countPredictions(predictHPY(N,top,bot), [0,1,2,3,4]) for top in [True,False] for bot in [True,False]]
  (chisq, pval) = stats.chi2_contingency(data)
  report = [
    "Expected: Samples from four equal distributions",
    "Observed:"]
  i = 0
  for top in ["Collapsed", "Uncollapsed"]:
    for bot in ["Collapsed", "Uncollapsed"]:
      report += "  (%s, %s): %s" % (top, bot, data[i])
      i += 1
  report += [
    "Chi^2   : " + str(chisq),
    "P value : " + str(pval)]
  return TestResult("TestHPYMem1", pval, "\n".join(report))

def testHPYMem1(N):
  if hasattr(stats, 'chi2_contingency'):
    return doTestHPYMem1(N)
  else:
    print "---TestHPYMem1 skipped for lack of scipy.stats.chi2_contingency"
    return reportPassage("TestHPYMem1")

def testGeometric1(N):
  ripl = RIPL()
  ripl.assume("alpha1","(gamma 5.0 2.0)")
  ripl.assume("alpha2","(gamma 5.0 2.0)")
  ripl.assume("p", "(beta alpha1 alpha2)")
  ripl.assume("geo","(lambda (p) (branch (bernoulli p) (lambda () 1) (lambda () (plus 1 (geo p)))))")
  ripl.predict("(geo p)",label="pid")

  predictions = collectSamples(ripl,"pid",N)

  k = 128
  ans = [(n,math.pow(2,-n)) for n in range(1,k)]
  return reportKnownDiscrete("TestGeometric1", ans, predictions)

def testTrig1(N):
  ripl = RIPL()
  ripl.assume("sq","(lambda (x) (* x x))")
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("a","(sq (sin x))")
  ripl.assume("b","(sq (cos x))")
  ripl.predict("(+ a b)")
  for i in range(N/10):
    ripl.infer(10,kernel="mh")
    assert abs(ripl.report(5) - 1) < .001
  return reportPassage("TestTrig1")

def testForget1():
  ripl = RIPL()

  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("f","(lambda (y) (normal y 1.0))")
  ripl.assume("g","(lambda (z) (normal z 2.0))")

  ripl.predict("(f 1.0)",label="id1")
  ripl.observe("(g 2.0)",3.0,label="id2")
  ripl.observe("(g 3.0)",3.0,label="id3")

  ripl.forget("id1")
  ripl.forget("id2")
  ripl.forget("id3")

  real_sivm = ripl.sivm.core_sivm.engine
  assert real_sivm.get_entropy_info()["unconstrained_random_choices"] == 1
  assert real_sivm.logscore() < 0
  return reportPassage("TestForget1")

# This is the original one that fires an assert, when the (flip) has 0.0 or 1.0 it doesn't fail
def testReferences1(N):
  ripl = RIPL()
  ripl.assume("draw_type1", "(make_crp 1.0)")
  ripl.assume("draw_type0", "(if (flip) draw_type1 (lambda () 1))")
  ripl.assume("draw_type2", "(make_dir_mult 1 1)")
  ripl.assume("class", "(if (flip) (lambda (name) (draw_type0)) (lambda (name) (draw_type2)))")
  ripl.predict("(class 1)")
  ripl.predict("(flip)")
  # TODO What is trying to test?  The address in the logging infer refers to the bare (flip).
  predictions = collectSamples(ripl,6,N)
  ans = [(True,0.5), (False,0.5)]
  return reportKnownDiscrete("TestReferences1", ans, predictions)

#
def testReferences2(N):
  ripl = RIPL()
  ripl.assume("f", "(if (flip 0.5) (make_dir_mult 1 1) (lambda () 1))")
  ripl.predict("(f)")
#  ripl.predict("(flip)",label="pid")

  predictions = collectSamples(ripl,2,N)
  ans = [(True,0.75), (False,0.25)]
  return reportKnownDiscrete("TestReferences2", ans, predictions)

def testMemoizingOnAList():
  ripl = RIPL()
  ripl.assume("G","(mem (lambda (x) 1))")
  ripl.predict("(G (list 0))")
  predictions = collectSamples(ripl,2,1)
  assert predictions == [1]
  return reportPassage("TestMemoizingOnAList")

def testOperatorChanging(N):
  ripl = RIPL()
  ripl.assume("f","(mem (lambda () (flip)))")
  ripl.assume("op1","(if (flip) flip (lambda () (f)))")
  ripl.assume("op2","(if (op1) op1 (lambda () (op1)))")
  ripl.assume("op3","(if (op2) op2 (lambda () (op2)))")
  ripl.assume("op4","(if (op3) op2 op1)")
  ripl.predict("(op4)")
  ripl.observe("(op4)",True)
  predictions = collectSamples(ripl,6,N,kernel="mh")
  ans = [(True,0.75), (False,0.25)]
  return reportKnownDiscrete("TestOperatorChanging", ans, predictions)

def testObserveAPredict0(N):
  ripl = RIPL()
  ripl.assume("f","(if (flip) (lambda () (flip)) (lambda () (flip)))")
  ripl.predict("(f)")
  ripl.observe("(f)","true")
  ripl.predict("(f)")
  predictions = collectSamples(ripl,2,N)
  ans = [(True,0.5), (False,0.5)]
  return reportKnownDiscrete("TestObserveAPredict0", ans, predictions)


### These tests are illegal Venture programs, and cause PGibbs to fail because
# when we detach for one slice, a node may think it owns its value, but then
# when we constrain we reclaim it and delete it, so it ends up getting deleted
# twice.

# def testObserveAPredict1(N):
#   ripl = RIPL()
#   ripl.assume("f","(if (flip 0.0) (lambda () (flip)) (mem (lambda () (flip))))")
#   ripl.predict("(f)")
#   ripl.observe("(f)","true")
#   ripl.predict("(f)")
#   predictions = collectSamples(ripl,2,N)
#   ans = [(True,0.75), (False,0.25)]
#   return reportKnownDiscrete("TestObserveAPredict1", ans, predictions)


# def testObserveAPredict2(N):
#   ripl = RIPL()
#   ripl.assume("f","(if (flip) (lambda () (normal 0.0 1.0)) (mem (lambda () (normal 0.0 1.0))))")
#   ripl.observe("(f)","1.0")
#   ripl.predict("(* (f) 100)")
#   predictions = collectSamples(ripl,3,N)
#   mean = float(sum(predictions))/len(predictions) if len(predictions) > 0 else 0
#   print "---TestObserveAPredict2---"
#   print "(25," + str(mean) + ")"
#   print "(note: true answer is 50, but program is illegal and staleness is correct behavior)"


def testBreakMem(N):
  ripl = RIPL()
  ripl.assume("pick_a_stick","""
(lambda (sticks k)
  (if (bernoulli (sticks k))
      k
      (pick_a_stick sticks (plus k 1))))
""")
  ripl.assume("d","(uniform_continuous 0.4 0.41)")

  ripl.assume("f","(mem (lambda (k) (beta 1.0 (times k d))))")
  ripl.assume("g","(lambda () (pick_a_stick f 1))")
  ripl.predict("(g)")
  ripl.infer(N)
  return reportPassage("TestBreakMem")

def testHPYLanguageModel1(N):
  ripl = RIPL()
  loadPYMem(ripl)

  # 5 letters for now
  ripl.assume("G_init","(make_sym_dir_mult 0.5 5)")

  # globally shared parameters for now
  ripl.assume("alpha","(gamma 1.0 1.0)")
  ripl.assume("d","(uniform_continuous 0.0 0.01)")

  # G(letter1 letter2 letter3) ~ pymem(alpha,d,G(letter2 letter3))
  ripl.assume("H","(mem (lambda (a) (pymem alpha d G_init)))")

  ripl.assume("noisy_true","(lambda (pred noise) (flip (if pred 1.0 noise)))")

  atoms = [0, 1, 2, 3, 4] * 4;

  for i in range(1,len(atoms)):
    ripl.observe("""
(noisy_true
  (atom_eq
    ((H atom<%d>))
    atom<%d>)
  0.001)
""" % (atoms[i-1],atoms[i]), "true")

  ripl.predict("((H atom<0>))",label="pid")

  predictions = collectSamples(ripl,"pid",N)
  ans = [(0,0.03), (1,0.88), (2,0.03), (3,0.03), (4,0.03)]
  return reportKnownDiscrete("testHPYLanguageModel1 (approximate)", ans, predictions)

def testHPYLanguageModel2(N):
  ripl = RIPL()
  loadPYMem(ripl)

  # 5 letters for now
  ripl.assume("G_init","(make_sym_dir_mult 0.5 5)")

  # globally shared parameters for now
  ripl.assume("alpha","(gamma 1.0 1.0)")
  ripl.assume("d","(uniform_continuous 0.0 0.01)")

  # G(letter1 letter2 letter3) ~ pymem(alpha,d,G(letter2 letter3))
  ripl.assume("G","""
(mem (lambda (context)
  (if (is_pair context)
      (pymem alpha d (G (rest context)))
      (pymem alpha d G_init))))
""")

  ripl.assume("noisy_true","(lambda (pred noise) (flip (if pred 1.0 noise)))")

  atoms = [0, 1, 2, 3, 4] * 4;

  for i in range(1,len(atoms)):
    ripl.observe("""
(noisy_true
  (atom_eq
    ((G (list atom<%d>)))
    atom<%d>)
  0.001)
""" % (atoms[i-1],atoms[i]), "true")

  ripl.predict("((G (list atom<0>)))",label="pid")

  predictions = collectSamples(ripl,"pid",N)
  ans = [(0,0.03), (1,0.88), (2,0.03), (3,0.03), (4,0.03)]
  return reportKnownDiscrete("testHPYLanguageModel2 (approximate)", ans, predictions)

def testGoldwater1(N):
  v = RIPL()

  #brent = open("brent_ratner/br-phono.txt", "r").readlines()
  #brent = [b.strip().split() for b in brent]
  #brent = ["".join(i) for i in brent]
  #brent = ["aaa", "bbb", "aaa", "bbb"]
  #brent = brent[:2]
  #brent = "".join(brent)
#  brent = ["catanddog", "dogandcat", "birdandcat","dogandbird","birdcatdog"]
  brent = ["aba","ab"]

  iterations = 100
  parameter_for_dirichlet = 1
#  n = 2 #eventually implement option to set n
  alphabet = "".join(set("".join(list(itertools.chain.from_iterable(brent)))))
  d = {}
  for i in xrange(len(alphabet)): d[alphabet[i]] = i

  v.assume("parameter_for_dirichlet", str(parameter_for_dirichlet))
  v.assume("alphabet_length", str(len(alphabet)))

  v.assume("sample_phone", "(make_sym_dir_mult parameter_for_dirichlet alphabet_length)")
  v.assume("sample_word_id", "(make_crp 1.0)")

  v.assume("sample_letter_in_word", """
(mem (lambda (word_id pos)
  (sample_phone)))
""")
#7
  v.assume("is_end", """
(mem (lambda (word_id pos)
  (flip .3)))
""")

  v.assume("get_word_id","""
(mem (lambda (sentence sentence_pos)
  (branch (= sentence_pos 0)
    (lambda () (sample_word_id))
    (lambda ()
      (branch (is_end (get_word_id sentence (- sentence_pos 1))
                      (get_pos sentence (- sentence_pos 1)))
        (lambda () (sample_word_id))
        (lambda () (get_word_id sentence (- sentence_pos 1))))))))
""")

  v.assume("get_pos","""
(mem (lambda (sentence sentence_pos)
  (branch (= sentence_pos 0)
    (lambda () 0)
    (lambda ()
      (branch (is_end (get_word_id sentence (- sentence_pos 1))
                      (get_pos sentence (- sentence_pos 1)))
        (lambda () 0)
        (lambda () (+ (get_pos sentence (- sentence_pos 1)) 1)))))))
""")

  v.assume("sample_symbol","""
(mem (lambda (sentence sentence_pos)
  (sample_letter_in_word (get_word_id sentence sentence_pos) (get_pos sentence sentence_pos))))
""")

#  v.assume("noise","(gamma 1 1)")
  v.assume("noise",".01")
  v.assume("noisy_true","(lambda (pred noise) (flip (if pred 1.0 noise)))")


  for i in range(len(brent)): #for each sentence
    for j in range(len(brent[i])): #for each letter
      v.predict("(sample_symbol %d %d)" %(i, j))
      v.observe("(noisy_true (atom_eq (sample_symbol %d %d) atom<%d>) noise)" %(i, j,d[str(brent[i][j])]), "true")

  v.infer(N)
  return reportPassage("TestGoldwater1")


def testMemHashFunction1(A,B):
  ripl = RIPL()
  ripl.assume("f","(mem (lambda (a b) (normal 0.0 1.0)))")
  for a in range(A):
    for b in range(B):
      ripl.observe("(f %d %d)" % (a,b),"0.5")
  return reportPassage("TestMemHashFunction(%d,%d)" % (A,B))


###########################
###### DSELSAM (madness) ##
###########################
def testDHSCRP1(N):
  ripl = RIPL()

  ripl.assume("dpmem","""
(lambda (alpha base_dist)
  ((lambda (augmented_proc crp)
     (lambda () (augmented_proc (crp))))
   (mem (lambda (table) (base_dist)))
   (make_crp alpha)))
""")

#  ripl.assume("alpha","(gamma 1.0 1.0)")
  ripl.assume("alpha","1.0")
  ripl.assume("base_dist","(lambda () (categorical 0.2 0.2 0.2 0.2 0.2))")
  ripl.assume("f","(dpmem alpha base_dist)")

  ripl.predict("(f)",label="pid")

  observeCategories(ripl,[2,2,5,1,0])

  predictions = collectSamples(ripl,"pid",N)
  ans = [(0,2.2), (1,2.2), (2,5.2), (3,1.2), (4,0.2)]
  return reportKnownDiscrete("TestDHSCRP1", ans, predictions)

def testDHSCRP2(N):
  ripl = RIPL()
  loadDPMem(ripl)

  ripl.assume("alpha","1.0")

  ripl.assume("base_dist","(lambda () (categorical 0.2 0.2 0.2 0.2 0.2))")
  ripl.assume("f","(u_dpmem alpha base_dist)")

  ripl.predict("(f)",label="pid")

  observeCategories(ripl,[2,2,5,1,0])

  predictions = collectSamples(ripl,"pid",N)
  ans = [(0,2.2), (1,2.2), (2,5.2), (3,1.2), (4,0.2)]
  return reportKnownDiscrete("TestDHSCRP2", ans, predictions)





def testPGibbsBlockingMHHMM1(N):
  ripl = RIPL()

  ripl.assume("x0","(scope_include 0 0 (normal 0.0 1.0))")
  ripl.assume("x1","(scope_include 0 1 (normal x0 1.0))")
  ripl.assume("x2","(scope_include 0 2 (normal x1 1.0))")
  ripl.assume("x3","(scope_include 0 3 (normal x2 1.0))")
  ripl.assume("x4","(scope_include 0 4 (normal x3 1.0))")

  ripl.assume("y0","(normal x0 1.0)")
  ripl.assume("y1","(normal x1 1.0)")
  ripl.assume("y2","(normal x2 1.0)")
  ripl.assume("y3","(normal x3 1.0)")
  ripl.assume("y4","(normal x4 1.0)")

  ripl.observe("y0",1.0)
  ripl.observe("y1",2.0)
  ripl.observe("y2",3.0)
  ripl.observe("y3",4.0)
  ripl.observe("y4",5.0)
  ripl.predict("x4")

  predictions = collectSamplesWith(ripl,16,N,{"kernel":"pgibbs","transitions":10,"scope":0,"block":"ordered"})
  reportKnownMeanVariance("TestPGibbsBlockingMHHMM1", 390/89.0, 55/89.0, predictions)
  cdf = stats.norm(loc=390/89.0, scale=math.sqrt(55/89.0)).cdf
  return reportKnownContinuous("TestPGibbsBlockingMHHMM1", cdf, predictions, "N(4.382, 0.786)")

##########

