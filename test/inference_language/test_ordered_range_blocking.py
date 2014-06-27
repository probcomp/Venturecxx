from venture.test.config import get_ripl

def testOrderedRangeBlockingExample():
  ripl = get_ripl()
  ripl.assume("a", "(scope_include 0 0 (normal 0.0 1.0))", label="a")
  ripl.assume("b", "(scope_include 0 1 (normal 1.0 1.0))", label="b")
  ripl.assume("c", "(scope_include 0 2 (normal 2.0 1.0))", label="c")
  ripl.assume("d", "(scope_include 0 3 (normal 3.0 1.0))", label="d")
  olda = ripl.report("a")
  oldb = ripl.report("b")
  oldc = ripl.report("c")
  oldd = ripl.report("d")
  # Should change b and c.
  ripl.sivm.core_sivm.engine.infer({"transitions":3, "kernel":"pgibbs", "scope":0, "block":"ordered_range", "min_block":1, "max_block":2, "particles": 10})
  newa = ripl.report("a")
  newb = ripl.report("b")
  newc = ripl.report("c")
  newd = ripl.report("d")
  assert olda == newa
  assert not oldb == newb
  assert not oldc == newc
  assert oldd == newd

