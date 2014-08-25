from nose.tools import eq_
from venture.test.config import get_ripl, on_inf_prim, broken_in

@broken_in('puma', 'zip SP not implemented in Puma')
@on_inf_prim("none")
def testZip1():
  eq_(get_ripl().predict("(zip)"), [])

@broken_in('puma', 'zip SP not implemented in Puma')
@on_inf_prim("none")
def testZip2():
  eq_(get_ripl().predict("(zip (list 1))"), [[1.0]])

@broken_in('puma', 'zip SP not implemented in Puma')
@on_inf_prim("none")
def testZip3():
  '''Should work with any # of input lists. Arrays, lists, and vectors should work'''
  pred = "(zip (array 1 2 3) (list 4 5 6) (vector 7 8 9))"
  res = [[1.0,4.0,7.0], [2.0,5.0,8.0], [3.0,6.0,9.0]]
  eq_(get_ripl().predict(pred), res)

@broken_in('puma', 'zip SP not implemented in Puma')
@on_inf_prim("none")
def testZip4():
  '''If one list is shorter, truncate the output'''
  pred = "(zip (array 1 2 3) (list 4 5 6) (vector 7 8))"
  res = [[1.0,4.0,7.0], [2.0,5.0,8.0]]
  eq_(get_ripl().predict(pred), res)
