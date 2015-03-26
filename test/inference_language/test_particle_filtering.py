import scipy.stats

from venture.test.config import get_ripl, on_inf_prim

# TODO Rewrite this to use mem like one normally would.  Right now
# it's metaprogrammed because freeze is only known to work on
# directives.

@on_inf_prim("resample")
def testHMMParticleSmoke():
  num_particles = 3
  num_steps = 10

  ripl = get_ripl()
  ripl.infer("(resample %s)" % num_particles)

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

  # TODO What, actually, are the distributions we expect?  Can a
  # version of this (with more particles?) be a statistical test?
