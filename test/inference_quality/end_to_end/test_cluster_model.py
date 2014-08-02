from nose.plugins.attrib import attr
from nose.tools import assert_less, assert_greater

from venture.test.config import get_ripl, on_inf_prim

def mean(xs): return sum(xs) / float(len(xs))

@attr("slow")    
@on_inf_prim("mh")
def testCRPMixSimple1():
  """Makes sure basic clustering model behaves reasonably"""
  ripl = get_ripl()

  ripl.assume('get_cluster_mean', "(mem (lambda (cluster) (uniform_continuous -10.0 10.0)))")
  ripl.predict("(get_cluster_mean 1)",label="cmean")
  
  ripl.observe("(normal (get_cluster_mean 1) 1)","5")

  B = 50
  T = 100

  mus = []

  for _ in range(T):
    ripl.infer(B)
    mus.append(ripl.report("cmean"))

  assert_less(mean(mus),5.5)
  assert_greater(mean(mus),4.5)

