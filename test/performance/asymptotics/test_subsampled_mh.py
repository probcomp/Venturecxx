import scipy.stats
from nose.plugins.attrib import attr

import venture.value.dicts as val
from venture.test.config import get_ripl, broken_in, on_inf_prim
import venture.test.timing as timing

@attr('slow')
@broken_in('puma', "subsampled_mh is only implemented in Lite")
@on_inf_prim("subsampled_mh")
def testMVNAsymptotics():
  def particulate(num_obs, epsilon):
    ripl = get_ripl()
    ripl.load_prelude()
    ripl.assume("mu", "(multivariate_normal (zeros 2) (eye 2))")
    # A slow procedure to compute f(m) = m[0:2] * 1.0
    ripl.assume("f", "(lambda (m) (map (lambda (i) (* 1.0 (lookup m i))) (range 0 2)))")
    ripl.assume("y", "(lambda () (multivariate_normal (f mu) (eye 2)))")
    for _ in range(num_obs):
      ripl.observe("(y)", val.vector(scipy.stats.norm.rvs(0, 1.0, 2)))
    ripl.infer("(mh default all 1)")

    def do_infer():
      ripl.infer("(subsampled_mh default all 10 3 %f false 0 false 10)" % epsilon)

    return do_infer

  timing.assertConstantTime(lambda n: particulate(n, 0.5),
      verbose=True, acceptable_duration=100, desired_sample_ct=40)

  timing.assertConstantTime(lambda n: particulate(n, 0.1),
      verbose=True, acceptable_duration=100, desired_sample_ct=40)

