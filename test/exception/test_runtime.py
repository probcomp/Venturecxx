from nose.tools import raises
from venture.test.config import get_ripl, backend
from testconfig import config
from venture.lite.exception import VentureError

@backend('lite')
@raises(VentureError)
def testSymbolNotFound():
  ripl = get_ripl()
  ripl.predict('a')

@backend('lite')
@raises(VentureError)
def testDoubleAssume():
  ripl = get_ripl()
  ripl.assume('a', 1)
  ripl.assume('a', 1)

@backend('lite')
@raises(VentureError)
def testNoSPRef():
  ripl = get_ripl()
  ripl.predict('(1 + 1)')

@backend('lite')
@raises(VentureError)
def testLambda():
  ripl = get_ripl()
  ripl.assume('err', '(lambda () a)')
  ripl.predict('(err)')

@backend('lite')
@raises(VentureError)
def testLargeStack():
  ripl = get_ripl()
  ripl.assume('f', '(lambda (i) (if (= i 0) a (f (- i 1))))')
  ripl.predict('(f 20)')

