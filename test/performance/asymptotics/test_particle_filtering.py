from venture.test.config import get_ripl
import venture.test.timing as timing
import scipy.stats
from nose.plugins.attrib import attr

# TODO Rewrite this to use mem like one normally would.  Right now
# it's metaprogrammed because freeze is only known to work on
# directives.

def loadHMMParticleAsymptoticProgram1(M, num_particles):
  """Easiest possible HMM asymptotic test for particle filtering"""
  ripl = get_ripl()
  ripl.infer("(resample %s)" % num_particles)

  ripl.assume("f","""
(mem (lambda (i)
  (if (eq i 0)
    (scope_include (quote states) 0 (normal 0.0 1.0))
    (scope_include (quote states) i (normal (f (- i 1)) 1.0)))))
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
# O(N log N) to infer
@attr('slow')
def testHMMParticleAsymptotics1():
  num_particles = 5
  def particulate(num_steps):
    ripl = get_ripl()
    ripl.infer("(resample %s)" % num_particles)
#    ripl = loadHMMParticleAsymptoticProgram1(num_steps, 5)

    def do_filter():
      for m in range(num_steps):
        newValue = scipy.stats.norm.rvs(0,1.0)
        if m == 0:
          ripl.assume("state_0", "(normal 0.0 1.0)", label="st0")
        else:
          ripl.assume("state_%d" % m, "(normal state_%d 1.0)" % (m-1), label="st%s" % m)
        ripl.observe("(normal state_%d 1.0)" % m, newValue)
        if m > 0:
          ripl.freeze("st%s" % (m-1))
        ripl.infer("(resample %s)" % num_particles)

    return do_filter

  timing.assertLinearTime(particulate)
