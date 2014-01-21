

def loadChurchPairProgram(K):
  ripl = RIPL()
  ripl.assume("make_church_pair","(lambda (x y) (lambda (f) (if (= f 0) (lambda () x) (lambda () y))))")
  ripl.assume("church_pair_lookup","(lambda (cp n) (if (= n 0) (lambda () (cp 0)) (lambda () (church_pair_lookup (cp 1)))))")
  ripl.assume("cp0","(make_church_pair (flip 0.5) 0)")
    
  for i in range(K):
    ripl.assume('cp%d' % (i+1), '(make_church_pair (flip) cp%d)' % i)

  ripl.predict('(church_pair_lookup cp%d %d)' % (N, N))
  return ripl

# O(N) forwards
# O(1) to infer
def testCP1():

  Ks = [pow(2,k) for k in range(2,10)]

  inferTimes = []
  N = 100

  for K in Ks:
    ripl = loadCPProgram(K)
    start = time.clock()
    ripl.infer(N)
    end = time.clock()
    inferTimes.append(end - start)

  assert (max(inferTimes) / min(inferTimes)) < 3

def loadReferencesProgram(K):
  ripl.assume("cp0","(list (make_ref (flip)))")
    
  for i in range(K):
    ripl.assume('cp%d' % (i+1), '(pair (make_ref (flip)) cp%d)' % i)

  ripl.predict('(lookup cp%d %d)' % (N, N))
  return ripl

# O(N) forwards
# O(1) to infer
# (this could be reused from testChurchPairProgram
def testReferencesProgram():
  Ks = [pow(2,k) for k in range(2,10)]

  inferTimes = []
  N = 100

  for K in Ks:
    ripl = loadReferencesProgram(K)
    start = time.clock()
    ripl.infer(N)
    end = time.clock()
    inferTimes.append(end - start)

  assert (max(inferTimes) / min(inferTimes)) < 3
