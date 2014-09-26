from nose.tools import raises
from venture.test.config import get_ripl, broken_in, on_inf_prim
from venture.exception import VentureException

@broken_in('puma')
@on_inf_prim("none")
@raises(VentureException)
def testSymbolNotFound():
  ripl = get_ripl()
  ripl.predict('a')

@broken_in('puma')
@on_inf_prim("none")
@raises(VentureException)
def testDoubleAssume():
  ripl = get_ripl()
  ripl.assume('a', 1)
  ripl.assume('a', 1)

@broken_in('puma')
@on_inf_prim("none")
@raises(VentureException)
def testNoSPRef():
  ripl = get_ripl()
  ripl.predict('(1 + 1)')

@broken_in('puma')
@on_inf_prim("none")
@raises(VentureException)
def testLambda():
  ripl = get_ripl()
  ripl.assume('err', '(lambda () a)')
  ripl.predict('(err)')

@broken_in('puma')
@on_inf_prim("none")
@raises(VentureException)
def testLargeStack():
  ripl = get_ripl()
  ripl.assume('f', '(lambda (i) (if (= i 0) a (f (- i 1))))')
  ripl.predict('(f 20)')

@broken_in('puma')
@on_inf_prim("none")
@raises(VentureException)
def testTooFewArgs():
  ripl = get_ripl()
  ripl.predict('(-)')

@broken_in('puma')
@on_inf_prim("none")
@raises(VentureException)
def testTooManyArgs():
  ripl = get_ripl()
  ripl.predict('(- 1 1 1)')

@broken_in('puma')
@on_inf_prim("none")
def testExceptionAnnotated():
  ripl = get_ripl()
  try:
    ripl.predict('a')
  except VentureException as e:
    assert(hasattr(e, 'annotated') and e.annotated)

