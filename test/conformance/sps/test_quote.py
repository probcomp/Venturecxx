from nose import SkipTest
from nose.tools import eq_
from venture.test.config import get_ripl, on_inf_prim

@on_inf_prim("none")
def testQuoteSmoke1():
  eq_(get_ripl().predict("(quote foo)"), "foo")

@on_inf_prim("none")
def testQuoteSmoke2():
  assert get_ripl().predict("(is_symbol (quote foo))")

@on_inf_prim("none")
def testQuoteSmoke3():
  assert get_ripl().predict("(is_array (quote (foo bar)))")

@on_inf_prim("none")
def testQuoteSmoke4():
  eq_(get_ripl().predict("(lookup (quote (foo bar)) 0)"), "foo")

@on_inf_prim("none")
def testQuoteIf():
  "Quote should suppress macroexpansion"
  raise SkipTest("This fails because the stack's \"desugaring\" is applied even to quoted expressions.  Oops.  Issue: https://app.asana.com/0/9277419963067/10442847514597")
  eq_(get_ripl().predict("(lookup (quote (if (flip) 0 1)) 0)"), "if")
