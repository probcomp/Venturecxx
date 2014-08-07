from numbers import Number
from venture.test.stats import statisticalTest, reportKnownDiscrete
from venture.test.config import get_ripl, collectSamples, on_inf_prim
from venture.ripl import Ripl
from nose.tools import eq_

@on_inf_prim("none")
def testRIPL():
  assert isinstance(get_ripl(), Ripl)

@on_inf_prim("none")
def testConstant():
  eq_(1, get_ripl().predict(1))

@on_inf_prim("none")
def testLambda():
  eq_(2, get_ripl().predict("((lambda (x) x) 2)"))

@on_inf_prim("none")
def testTriviality1():
  eq_(4, get_ripl().predict("(+ 2 2)"))

@on_inf_prim("none")
def testTriviality2():
  eq_(2, get_ripl().predict("(- 4 2)"))

@on_inf_prim("none")
def testIf1():
  eq_(2, get_ripl().predict("(if true 2 3)"))

@on_inf_prim("none")
def testIf2():
  eq_(3, get_ripl().predict("(if false 2 3)"))

@on_inf_prim("none")
def testIf3():
  ripl = get_ripl()
  ripl.assume("z", "1")
  ripl.assume("y", "2")
  eq_(1, ripl.predict("(if true z y)"))

@on_inf_prim("none")
def testFlip1():
  assert isinstance(get_ripl().predict("(bernoulli 0.5)"), Number)

@statisticalTest
def testFlip2():
  ripl = get_ripl()
  ripl.predict("(bernoulli 0.5)",label="pid")
  predictions = collectSamples(ripl, "pid")
  return reportKnownDiscrete([[True, 0.5], [False, 0.5]], predictions)

@on_inf_prim("none")
def testAtom():
  assert get_ripl().predict("(is_atom atom<1>)")
