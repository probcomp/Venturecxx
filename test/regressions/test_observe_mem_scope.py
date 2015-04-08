from nose.tools import eq_

import venture.lite.value as val
from venture.test.config import get_ripl, broken_in

@broken_in("puma", "No introspection on blocks in scope")
def testScopeObservedThroughMem1():
  r = get_ripl()
  r.assume("frob", "(mem (lambda (x) (flip 0.5)))")
  r.observe("(frob 1)", True)
  r.predict("(tag (quote foo) 0 (frob 1))")
  trace = r.sivm.core_sivm.engine.getDistinguishedTrace()
  scope = trace._normalizeEvaluatedScopeOrBlock(val.VentureSymbol("foo")) # pylint:disable=protected-access
  eq_(1, len(trace.getAllNodesInScope(scope)))
  r.infer("(incorporate)")
  eq_(0, len(trace.getAllNodesInScope(scope)))

@broken_in("puma", "No introspection on blocks in scope")
def testScopeObservedThroughMem2():
  """The way resample happened to be implemented in Lite when I wrote
this test, it had the effect of undoing [infer (incorporate)] for all
observations.  This was detected through a horrible mess involving mem.

  """
  r = get_ripl()
  r.assume("frob", "(mem (lambda (x) (flip 0.5)))")
  r.observe("(frob 1)", True)
  trace = r.sivm.core_sivm.engine.getDistinguishedTrace()
  scope = trace._normalizeEvaluatedScopeOrBlock(val.VentureSymbol("foo")) # pylint:disable=protected-access
  eq_(0, trace.numBlocksInScope(scope))
  r.infer("(incorporate)")
  r.predict("(frob 1)")
  r.infer("(resample 1)")
  r.predict("(tag (quote foo) 0 (frob 1))")
  trace = r.sivm.core_sivm.engine.getDistinguishedTrace()
  eq_(0, len(trace.getAllNodesInScope(scope)))

def testResamplingObservations():
  """The way resample happened to be implemented in Lite when I wrote
this test, it had the effect of undoing [infer (incorporate)] for all
observations.

  """
  r = get_ripl()
  r.assume("x", "(normal 0 1)")
  r.observe("x", 1)
  r.infer("(incorporate)")
  eq_(1, r.sample("x"))
  r.infer("(do (resample 1) (mh default all 1))")
  eq_(1, r.sample("x"))
