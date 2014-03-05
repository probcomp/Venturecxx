from venture.test.config import get_ripl, collectSamples
from nose.tools import assert_equal

def testPredictConstantBool1():
  ripl = get_ripl()
  ripl.predict("true",label="pid")
  assert ripl.report("pid")

def testPredictConstantBool2():
  ripl = get_ripl()
  ripl.predict("false",label="pid")
  assert not ripl.report("pid")

def testPredictConstantNumber1():
  ripl = get_ripl()
  ripl.predict("1",label="pid")
  assert_equal(ripl.report("pid"),1)

def testPredictConstantAtom1():
  ripl = get_ripl()
  ripl.predict("atom<5>",label="pid")
  assert_equal(ripl.report("pid"),5)

def testPredictNumeric1():
  ripl = get_ripl()
  ripl.predict("(+ 3 4)",label="pid")
  assert_equal(ripl.report("pid"),7)

def testPredictNumeric2():
  ripl = get_ripl()
  ripl.predict("(* 3 4)",label="pid")
  assert_equal(ripl.report("pid"),12)

def testPredictNumeric3():
  ripl = get_ripl()
  ripl.predict("(pow 2 4)",label="pid")
  assert_equal(ripl.report("pid"),16)

def testPredictCSP1():
  ripl = get_ripl()
  ripl.assume("f","(lambda (x) x)")
  ripl.predict("(f (pow 2 4))",label="pid")
  assert_equal(ripl.report("pid"),16)

def testPredictCSP2():
  ripl = get_ripl()
  ripl.assume("f","(lambda (x) (pow x 4))")
  ripl.predict("(f 2)",label="pid")
  assert_equal(ripl.report("pid"),16)

def testPredictCSP3():
  ripl = get_ripl()
  ripl.assume("f","(lambda (x y) (* x y))")
  ripl.predict("(f 5 7)",label="pid")
  assert_equal(ripl.report("pid"),35)

def testPredictCSP4():
  ripl = get_ripl()
  ripl.assume("f","(lambda (x y z ) (* (+ x y) z))")
  ripl.predict("(f 2 3 5)",label="pid")
  assert_equal(ripl.report("pid"),25)

def testPredictCSP5():
  ripl = get_ripl()
  ripl.assume("f","(lambda (x) (+ x 1))")
  ripl.predict("(f (f (f (f (f 0)))))",label="pid")
  assert_equal(ripl.report("pid"),5)

def testPredictCSP6():
  ripl = get_ripl()
  ripl.assume("f","(lambda (x y) (+ x y 1))")
  ripl.predict("(f (f 2 3) (f 1 2))",label="pid")
  assert_equal(ripl.report("pid"),11)

def testPredictArray1():
  ripl = get_ripl()
  ripl.assume("xs","(array 2 3 5 7)")
  ripl.predict("(* (lookup xs 0) (lookup xs 1))",label="pid")
  assert_equal(ripl.report("pid"),6)

def testPredictPair1():
  ripl = get_ripl()
  ripl.assume("xs","(pair 2 (pair 3 nil))")
  ripl.predict("(* (first xs) (first (rest xs)))",label="pid")
  assert_equal(ripl.report("pid"),6)

def testPredictList1():
  ripl = get_ripl()
  ripl.assume("xs","(list 2 3 4)")
  ripl.predict("(* (lookup xs 1) (lookup xs 2))",label="pid")
  assert_equal(ripl.report("pid"),12)
                    
