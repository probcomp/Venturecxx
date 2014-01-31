from venture.test.stats import *
import venture.test.timing as timing
import scipy.stats
from nose.plugins.attrib import attr

def loadHMMParticleAsymptoticProgram1(M):
  """Easiest possible HMM asymptotic test for particles"""
  ripl = get_ripl()

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
@attr('slow')
def testHMMParticleAsymptotics1():
#  from nose import SkipTest
#  raise SkipTest("Skipping testHMMParticleAsymptotics1: no linear regression test")

  def particulate(num_steps):
    ripl = loadHMMParticleAsymptoticProgram1(num_steps)
    return lambda : ripl.infer({"kernel":"pgibbs","scope":"states","block":"ordered","transitions":5,"particles":10})

  timing.assertLinearTime(particulate)
