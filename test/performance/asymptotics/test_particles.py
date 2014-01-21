from venture.test.stats import *
from testconfig import config
import scipy.stats
import time

def loadHMMParticleAsymptoticProgram1(M):
  """Easiest possible HMM asymptotic test for particles"""
  N = config["num_samples"]
  ripl = config["get_ripl"]()

  ripl.assume("f","""
(mem (lambda (i)
  (if (eq i 0)
    (scope_include (quote states) 0 (normal 0.0 1.0))
    (scope_include (quote states) i (normal (f (minus i 1)) 1.0)))))
""")
  ripl.assume("g","""
(mem (lambda (i)
  (normal (f i) 1.0)))
""")

  previousValue = 0.0
  for m in range(M):
    newValue = scipy.stats.norm.rvs(previousValue,1.0)
    ripl.observe("(g %d)" % m,"%d" % newValue)
    previousValue = newValue

  return ripl


# O(N) forwards
# O(N) to infer
def testHMMParticleAsymptotics1():
#  from nose import SkipTest
#  raise SkipTest("Skipping testHMMParticleAsymptotics1: no linear regression test")

  K = 5
  Ts = [2 * T for T in range(1,K+1)]
  N = 10

  inferTimes = []

  for T in Ts:
    ripl = loadHMMParticleAsymptoticProgram1(T)
    start = time.clock()
    ripl.infer({"kernel":"pgibbs","scope":"states","block":"ordered","transitions":N})
    end = time.clock()
    inferTimes.append(end - start)

  # TODO some kind of linear regression R-value 
  # (the run times should grow linearly in T)
  assert (max(inferTimes) / min(inferTimes)) < 2 * K

