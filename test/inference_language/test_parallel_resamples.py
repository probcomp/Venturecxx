from nose.tools import eq_
import threading
import scipy.stats

from venture.test.config import get_ripl, default_num_samples, gen_on_inf_prim
from venture.test.stats import statisticalTest, reportKnownContinuous

@gen_on_inf_prim("resample")
def testSynchronousIsSerial():
  yield checkSynchronousIsSerial, "resample"
  yield checkSynchronousIsSerial, "resample_serializing"

def checkSynchronousIsSerial(mode):
  numthreads = threading.active_count()
  r = get_ripl()
  eq_(numthreads, threading.active_count())
  r.infer("(%s 2)" % mode)
  eq_(numthreads, threading.active_count())

@gen_on_inf_prim("resample")
def testResamplingSmoke():
  for mode in ["", "_serializing", "_threaded", "_thread_ser", "_multiprocess"]:
    yield checkResamplingSmoke, mode

@statisticalTest
def checkResamplingSmoke(mode):
  n = default_num_samples()
  r = get_ripl()
  r.infer("(resample%s %s)" % (mode, n))
  stack_dicts = r.sivm.core_sivm.engine.sample_all(r._ensure_parsed_expression("(normal 0 1)"))
  predictions = [d["value"] for d in stack_dicts]
  return reportKnownContinuous(scipy.stats.norm(loc=0, scale=1).cdf, predictions, "N(0,1)")
