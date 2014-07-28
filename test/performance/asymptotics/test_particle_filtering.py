import scipy.stats
from nose.plugins.attrib import attr

from venture.test.config import get_ripl, broken_in
import venture.test.timing as timing

# TODO Rewrite this to use mem like one normally would.  Right now
# it's metaprogrammed because freeze is only known to work on
# directives.

@attr('slow')
@broken_in('lite', "freeze is only implemented in Puma")
def testHMMParticleAsymptotics1():
  num_particles = 5
  def particulate(num_steps):
    ripl = get_ripl()
    ripl.infer("(resample %s)" % num_particles)

    def do_filter():
      for m in range(num_steps):
        newValue = scipy.stats.norm.rvs(0,1.0)
        if m == 0:
          ripl.assume("state_0", "(normal 0.0 1.0)", label="st0")
        else:
          ripl.assume("state_%d" % m, "(normal state_%d 1.0)" % (m-1), label="st%s" % m)
        ripl.observe("(normal state_%d 1.0)" % m, newValue, label="obs%d" % m)
        if m > 0:
          ripl.freeze("st%s" % (m-1))
          ripl.forget("obs%d" % (m-1))
        if m > 1:
          ripl.forget("st%s" % (m-2))
        ripl.infer("(resample %s)" % num_particles)

    return do_filter

  timing.assertLinearTime(particulate, verbose=True, acceptable_duration=300, desired_sample_ct=40)
