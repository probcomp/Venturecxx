from nose.tools import raises

from venture.test.config import get_ripl, on_inf_prim
from venture.exception import VentureException

@on_inf_prim("none")
@raises(VentureException)
def testMissingOpenParen():
  ripl = get_ripl()
  ripl.predict('(')

@on_inf_prim("none")
@raises(VentureException)
def testMissingCloseParen():
  ripl = get_ripl()
  ripl.predict(')')


