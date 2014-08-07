from venture.test.config import get_ripl, on_inf_prim

@on_inf_prim("pgibbs")
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
  ripl.infer("(pgibbs 0 (ordered_range 1 2) 10 3)")
  newa = ripl.report("a")
  newb = ripl.report("b")
  newc = ripl.report("c")
  newd = ripl.report("d")
  assert olda == newa
  assert not oldb == newb
  assert not oldc == newc
  assert oldd == newd

