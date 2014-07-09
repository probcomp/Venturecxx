from nose.tools import raises
from venture.test.config import get_ripl
from testconfig import config
from venture.exception import VentureException

@raises(VentureException)
def testMissingOpenParen():
  ripl = get_ripl()
  ripl.predict('(')

@raises(VentureException)
def testMissingCloseParen():
  ripl = get_ripl()
  ripl.predict(')')


