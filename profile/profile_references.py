import cProfile
import sys
import venture.shortcuts as v
sys.setrecursionlimit(1000000) 

def loadReferencesProgram(K):
  ripl = v.make_lite_church_prime_ripl()
  ripl.assume("make_ref","(lambda (x) (lambda () x))")
  ripl.assume("deref","(lambda (r) (r))")

  ripl.assume("cp0","(list (make_ref (flip)))")
    
  for i in range(K):
    ripl.assume('cp%d' % (i+1), '(pair (make_ref (flip)) cp%d)' % i)

  ripl.predict('(deref (lookup cp%d %d))' % (K, K))
  return ripl

# O(N) forwards
# O(1) to infer
def profileReferencesProgram(K,N):
  ripl = loadReferencesProgram(K)
  cProfile.runctx("ripl.infer(%d)" % N,None,locals(),"profile_references.pyprof")

  
