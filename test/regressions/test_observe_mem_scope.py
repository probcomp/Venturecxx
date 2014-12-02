from nose.tools import eq_

import venture.lite.value as val
from venture.test.config import get_ripl, broken_in

@broken_in("puma") # Because no introspection on blocks in scope
def testScopeObservedThroughMem():
  r = get_ripl()
  r.assume("frob", "(mem (lambda (x) (flip 0.5)))")
  r.observe("(frob 1)", True)
  r.predict("(scope_include (quote foo) 0 (frob 1))")
  trace = r.sivm.core_sivm.engine.getDistinguishedTrace()
  scope = trace._normalizeEvaluatedScopeOrBlock(val.VentureSymbol("foo")) # pylint:disable=protected-access
  eq_(1, len(trace.getAllNodesInScope(scope)))
  r.infer("(incorporate)")
  eq_(0, len(trace.getAllNodesInScope(scope)))
