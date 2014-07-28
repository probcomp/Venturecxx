from nose.tools import raises
from venture.test.config import get_ripl, broken_in
from venture.lite.exception import VentureError

@broken_in('puma')
@raises(VentureError)
def testSymbolNotFound():
  ripl = get_ripl()
  ripl.predict('a')

@broken_in('puma')
@raises(VentureError)
def testDoubleAssume():
  ripl = get_ripl()
  ripl.assume('a', 1)
  ripl.assume('a', 1)

@broken_in('puma')
@raises(VentureError)
def testNoSPRef():
  ripl = get_ripl()
  ripl.predict('(1 + 1)')

@broken_in('puma')
@raises(VentureError)
def testLambda():
  ripl = get_ripl()
  ripl.assume('err', '(lambda () a)')
  ripl.predict('(err)')

@broken_in('puma')
@raises(VentureError)
def testLargeStack():
  ripl = get_ripl()
  ripl.assume('f', '(lambda (i) (if (= i 0) a (f (- i 1))))')
  ripl.predict('(f 20)')

@broken_in('puma')
@raises(VentureError)
def testTooFewArgs():
  ripl = get_ripl()
  ripl.predict('(-)')

@broken_in('puma')
@raises(VentureError)
def testTooManyArgs():
  ripl = get_ripl()
  ripl.predict('(- 1 1 1)')

