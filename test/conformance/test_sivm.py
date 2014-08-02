from venture.test.config import get_ripl, on_inf_prim
from nose.tools import assert_equal, assert_less

@on_inf_prim("none")
def testForget1():
  ripl = get_ripl()

  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("f","(lambda (y) (normal y 1.0))")
  ripl.assume("g","(lambda (z) (normal z 2.0))")

  ripl.predict("(f 1.0)",label="id1")
  ripl.observe("(g 2.0)",3.0,label="id2")
  ripl.observe("(g 3.0)",3.0,label="id3")

  ripl.forget("id1")
  ripl.forget("id2")
  ripl.forget("id3")

  # TODO this line is completely unforgiveable
  real_sivm = ripl.sivm.core_sivm.engine
  assert_equal(real_sivm.get_entropy_info()["unconstrained_random_choices"],1)
  assert_less(real_sivm.logscore(),0)
