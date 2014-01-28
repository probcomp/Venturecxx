from venture.test.stats import *
import time
import cProfile
import sys

sys.setrecursionlimit(1000000) 

def loadChurchPairProgram(K):
  ripl = get_ripl()

  ripl.assume("make_church_pair","(lambda (x y) (lambda (f) (if (= f 0) x y)))")
  ripl.assume("church_pair_lookup","(lambda (cp n) (if (= n 0) (cp 0) (church_pair_lookup (cp 1) (- n 1))))")
  ripl.assume("cp0","(make_church_pair (flip 0.5) 0)")
    
  for i in range(K):
    ripl.assume('cp%d' % (i+1), '(make_church_pair (flip) cp%d)' % i)

  ripl.predict('(church_pair_lookup cp%d %d)' % (K, K))
  return ripl


# O(N) forwards
# O(1) to infer
def testChurchPairProgram1():

  Ks = [pow(2,k) for k in range(2,11)]

  inferTimes = []
  N = 100

  for K in Ks:
    ripl = loadChurchPairProgram(K)
    start = time.clock()
    ripl.infer(N)
    end = time.clock()
    inferTimes.append(end - start)

  assert (max(inferTimes) / min(inferTimes)) < 3

def loadReferencesProgram(K):
  ripl = get_ripl()
  ripl.assume("make_ref","(lambda (x) (lambda () x))")
  ripl.assume("deref","(lambda (r) (r))")

  ripl.assume("cp0","(list (make_ref (flip)))")
    
  for i in range(K):
    ripl.assume('cp%d' % (i+1), '(pair (make_ref (flip)) cp%d)' % i)

  ripl.predict('(deref (lookup cp%d %d))' % (K, K))
  return ripl

# O(N) forwards
# O(1) to infer
# (this could be reused from testChurchPairProgram
def testReferencesProgram1():
  Ks = [pow(2,k) for k in range(2,11)]

  inferTimes = []
  N = 100

  for K in Ks:
    ripl = loadReferencesProgram(K)
    start = time.clock()
    ripl.infer(N)
    end = time.clock()
    inferTimes.append(end - start)

  assert (max(inferTimes) / min(inferTimes)) < 3
