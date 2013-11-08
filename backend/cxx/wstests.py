from venture.shortcuts import *
import math
import pdb

def SIVM():
  return make_church_prime_ripl()

def normalizeList(seq): 
  denom = sum(seq)
  if denom > 0: return [ float(x)/denom for x in seq]
  else: return [0 for x in seq]

def countPredictions(predictions, seq):
  return [predictions.count(x) for x in seq]

def rmsDifference(eps,ops): return math.sqrt(sum([ math.pow(x - y,2) for (x,y) in zip(eps,ops)]))
    
def printTest(testName,eps,ops):
  print "---Test: " + testName + "---"
  print "Expected: " + str(eps)
  print "Observed: " + str(ops)
  print "Root Mean Square Difference: " + str(rmsDifference(eps,ops))

def loggingInfer(sivm,address,T):
  predictions = []
  for t in range(T):
    sivm.infer(10, kernel="mh", use_global_scaffold=False)
    predictions.append(sivm.report(address))
#    print predictions[len(predictions)-1]
  return predictions

def runTests(N):
#  testBernoulli0(N)
  testBernoulli1(N)
  #testCategorical1(N)
  testMHNormal0(N)
  testMHNormal1(N)
  testStudentT0(N)
  testMem0(N)
  #testMem1(N)
  #testMem2(N)
  #testMem3(N)
  testSprinkler1(N)
  testSprinkler2(N)
  testGamma1(N)
  testIf1(N)
  testIf2(N)
  testBLOGCSI(N)
  testMHHMM1(N)
  testOuterMix1(N)
  testMakeSymDirMult1(N)
  testMakeSymDirMult2(N)
  testMakeUCSymDirMult1(N)
  testMap1(N)
  testLazyHMM1(N)
  testLazyHMMSP1(N)
  testStaleAAA1(N)
  testStaleAAA2(N)
  testEval1(N)
  testEval2(N)
  testEval3(N)
  testApply1(N)
  testExtendEnv1(N)
  testList1()
  testHPYMem1(N)
  testGeometric1(N)
  testTrig1(N)
  testForget1()
  testForget2()

def runTests2(N):
  testGeometric1(N)

def testBernoulli0(N):
  sivm = SIVM()
  sivm.assume("b", "((lambda () (bernoulli)))")
  sivm.predict("""
((biplex
  b
  (lambda () (normal 0.0 1.0))
  (lambda () ((lambda () (normal 10.0 1.0))))))
""");
  predictions = loggingInfer(sivm,2,N)
  mean = float(sum(predictions))/len(predictions) if len(predictions) > 0 else 0
  print "---TestBernoulli0---"
  print "(5.0," + str(mean) + ")"


def testBernoulli1(N):
  sivm = SIVM()
  sivm.assume("b", "((lambda () (bernoulli 0.7)))")
  sivm.predict("""
(branch
  b
  (lambda () (normal 0.0 1.0))
  (lambda () ((lambda () (normal 10.0 1.0)))))
""");
  predictions = loggingInfer(sivm,2,N)
  mean = float(sum(predictions))/len(predictions) if len(predictions) > 0 else 0
  print "---TestBernoulli1---"
  print "(3.0," + str(mean) + ")"

def testCategorical1(N):
  sivm = SIVM()
  sivm.assume("x", "(categorical 0.1 0.2 0.3 0.4)")
  sivm.assume("y", "(categorical 0.2 0.6 0.2)")
  sivm.predict("(plus x y)")

  predictions = loggingInfer(sivm,3,N)
  ps = [0.1 * 0.2, 
        0.1 * 0.6 + 0.2 * 0.2,
        0.1 * 0.2 + 0.2 * 0.6 + 0.3 * 0.2,
        0.2 * 0.2 + 0.3 * 0.6 + 0.4 * 0.2,
        0.3 * 0.2 + 0.4 * 0.6,
        0.4 * 0.2]
  eps = normalizeList(countPredictions(predictions, [0,1,2,3,4,5])) if N > 0 else [0 for x in range(6)]
  printTest("testCategorical1",ps,eps)

def testMHNormal0(N):
  sivm = SIVM()
  sivm.assume("a", "(normal 10.0 1.0)")
  sivm.observe("(normal a 1.0)", 14.0)
  sivm.predict("(normal a 1.0)")

  predictions = loggingInfer(sivm,3,N)
  mean = float(sum(predictions))/len(predictions) if len(predictions) > 0 else 0
  print "---TestMHNormal0---"
  print "(12.0," + str(mean) + ")"
    

def testMHNormal1(N):
  sivm = SIVM()
  sivm.assume("a", "(normal 10.0 1.0)")
  sivm.assume("b", "(normal a 1.0)")
  sivm.observe("((lambda () (normal b 1.0)))", 14.0)
  sivm.predict("""
(branch (lt a 100.0) 
        (lambda () (normal (plus a b) 1.0))
        (lambda () (normal (times a b) 1.0)))
""")

  predictions = loggingInfer(sivm,4,N)
  mean = float(sum(predictions))/len(predictions) if len(predictions) > 0 else 0
  print "---TestMHNormal1---"
  print "(23.9," + str(mean) + ")"

def testStudentT0(N):
  # Modeled on testMHNormal0, but I do not know what the answer is
  # supposed to be.  However, the run not crashing says something.
  sivm = SIVM()
  sivm.assume("a", "(student_t 1.0)")
  sivm.observe("(normal a 1.0)", 3.0)
  sivm.predict("(normal a 1.0)")
  predictions = loggingInfer(sivm,3,N)
  mean = float(sum(predictions))/len(predictions) if len(predictions) > 0 else 0
  print "---TestStudentT0---"
  print "(???," + str(mean) + ")"

def testMem0(N):
  sivm = SIVM()
  sivm.assume("f","(mem (lambda (x) (bernoulli 0.5)))")
  sivm.predict("(f (bernoulli 0.5))")
  sivm.predict("(f (bernoulli 0.5))")
  sivm.infer(N, kernel="mh", use_global_scaffold=False)
  print "Passed TestMem0"


def testMem1(N):
  sivm = SIVM()
  sivm.assume("f","(mem (lambda (arg) (plus 1 (categorical 0.4 0.6))))")
  sivm.assume("x","(f 1)")
  sivm.assume("y","(f 1)")
  sivm.assume("w","(f 2)")
  sivm.assume("z","(f 2)")
  sivm.assume("q","(plus 1 (categorical 0.1 0.9))")
  sivm.predict('(plus x y w z q)');

  predictions = loggingInfer(sivm,7,N)
  ps = [0.4 * 0.4 * 0.1, 0.6 * 0.6 * 0.9]
  eps = [ float(x) / N for x in countPredictions(predictions, [5,10])] if N > 0 else [0,0]
  printTest("TestMem1",ps,eps)

def testMem2(N):
  sivm = SIVM()
  sivm.assume("f","(mem (lambda (arg) (plus 1 (categorical 0.4 0.6))))")
  sivm.assume("g","((lambda () (mem (lambda (y) (f (plus y 1))))))")
  sivm.assume("x","(f ((branch (bernoulli 0.5) (lambda () (lambda () 1)) (lambda () (lambda () 1)))))")
  sivm.assume("y","(g ((lambda () 0)))")
  sivm.assume("w","((lambda () (f 2)))")
  sivm.assume("z","(g 1)")
  sivm.assume("q","(plus 1 (categorical 0.1 0.9))")
  sivm.predict('(plus x y w z q)');

  predictions = loggingInfer(sivm,8,N)
  ps = [0.4 * 0.4 * 0.1, 0.6 * 0.6 * 0.9]
  eps = [ float(x) / N for x in countPredictions(predictions, [5,10])] if N > 0 else [0,0]
  printTest("TestMem2",ps,eps)

def testMem3(N):
  sivm = SIVM()
  sivm.assume("f","(mem (lambda (arg) (plus 1 (categorical 0.4 0.6))))")
  sivm.assume("g","((lambda () (mem (lambda (y) (f (plus y 1))))))")
  sivm.assume("x","(f ((lambda () 1)))")
  sivm.assume("y","(g ((lambda () (branch (bernoulli 1.0) (lambda () 0) (lambda () 100)))))")
  sivm.assume("w","((lambda () (f 2)))")
  sivm.assume("z","(g 1)")
  sivm.assume("q","(plus 1 (categorical 0.1 0.9))")
  sivm.predict('(plus x y w z q)');

  predictions = loggingInfer(sivm,8,N)
  ps = [0.4 * 0.4 * 0.1, 0.6 * 0.6 * 0.9]
  eps = [ float(x) / N for x in countPredictions(predictions, [5,10])] if N > 0 else [0,0]
  printTest("TestMem3",ps,eps)

def testSprinkler1(N):
  sivm = SIVM()
  sivm.assume("rain","(bernoulli 0.2)")
  sivm.assume("sprinkler","(branch rain (lambda () (bernoulli 0.01)) (lambda () (bernoulli 0.4)))")
  sivm.assume("grassWet","""
(branch rain 
(lambda () (branch sprinkler (lambda () (bernoulli 0.99)) (lambda () (bernoulli 0.8))))
(lambda () (branch sprinkler (lambda () (bernoulli 0.9)) (lambda () (bernoulli 0.00001)))))
""")
  sivm.observe("grassWet", True)

  predictions = loggingInfer(sivm,1,N)
  ps = [.3577,.6433]
  eps = normalizeList(countPredictions(predictions, [True,False]))
  printTest("TestSprinkler1",ps,eps)

def testSprinkler2(N):
  # this test needs more iterations than most others, because it mixes badly
  N = N

  sivm = SIVM()
  sivm.assume("rain","(bernoulli 0.2)")
  sivm.assume("sprinkler","(bernoulli (branch rain (lambda () 0.01) (lambda () 0.4)))")
  sivm.assume("grassWet","""
(bernoulli (branch rain 
(lambda () (branch sprinkler (lambda () 0.99) (lambda () 0.8)))
(lambda () (branch sprinkler (lambda () 0.9) (lambda () 0.00001)))))
""")
  sivm.observe("grassWet", True)

  predictions = loggingInfer(sivm,1,N)
  ps = [.3577,.6433]
  eps = normalizeList(countPredictions(predictions, [True,False]))
  printTest("TestSprinkler2 (mixes terribly)",ps,eps)

def testGamma1(N):
  sivm = SIVM()
  sivm.assume("a","(gamma 10.0 10.0)")
  sivm.assume("b","(gamma 10.0 10.0)")
  sivm.predict("(gamma a b)")

  predictions = loggingInfer(sivm,3,N)
  mean = float(sum(predictions))/len(predictions) if len(predictions) > 0 else 0
  print "---TestMHGamma1---"
  print "(10000," + str(mean) + ")"

def testIf1(N):
  sivm = SIVM()
  sivm.assume('IF', '(lambda () branch)')
  sivm.assume('IF2', '(branch (bernoulli 0.5) IF IF)')
  sivm.predict('(IF2 (bernoulli 0.5) IF IF)')
  sivm.infer(N/10, kernel="mh", use_global_scaffold=False)
  print "Passed TestIf1()"

def testIf2(N):
  sivm = SIVM()
  sivm.assume('if1', '(branch (bernoulli 0.5) (lambda () branch) (lambda () branch))')
  sivm.assume('if2', '(branch (bernoulli 0.5) (lambda () if1) (lambda () if1))')
  sivm.assume('if3', '(branch (bernoulli 0.5) (lambda () if2) (lambda () if2))')
  sivm.assume('if4', '(branch (bernoulli 0.5) (lambda () if3) (lambda () if3))')
  sivm.infer(N/10, kernel="mh", use_global_scaffold=False)
  print "Passed TestIf2()"

def testBLOGCSI(N):
  sivm = SIVM()
  sivm.assume("u","(bernoulli 0.3)")
  sivm.assume("v","(bernoulli 0.9)")
  sivm.assume("w","(bernoulli 0.1)")
  sivm.assume("getParam","(lambda (z) (branch z (lambda () 0.8) (lambda () 0.2)))")
  sivm.assume("x","(bernoulli (branch u (lambda () (getParam w)) (lambda () (getParam v))))")
  
  predictions = loggingInfer(sivm,5,N)
  ps = [.596, .404]
  eps = normalizeList(countPredictions(predictions, [True, False]))
  printTest("TestBLOGCSI",ps,eps)


def testMHHMM1(N):
  sivm = SIVM()
  sivm.assume("f","""
(mem (lambda (i) (branch (eq i 0) (lambda () (normal 0.0 1.0)) (lambda () (normal (f (minus i 1)) 1.0)))))
""")
  sivm.assume("g","""
(mem (lambda (i) (normal (f i) 1.0)))
""")
  sivm.observe("(g 0)",1.0)
  sivm.observe("(g 1)",2.0)
  sivm.observe("(g 2)",3.0)
  sivm.observe("(g 3)",4.0)
  sivm.observe("(g 4)",5.0)
  sivm.predict("(f 4)")

  predictions = loggingInfer(sivm,8,N)
  mean = float(sum(predictions))/len(predictions) if len(predictions) > 0 else 0
  print "---TestMHHMM1---"
  print "(4.3ish," + str(mean) + ")"

def testOuterMix1(N):
  sivm = SIVM()
  sivm.predict("""
(branch (bernoulli 0.5) 
  (lambda ()
    (branch (bernoulli 0.5) (lambda () 2) (lambda () 3)))
  (lambda () 1))
""")

  predictions = loggingInfer(sivm,1,N)
  ps = [.5, .25,.25]
  eps = normalizeList(countPredictions(predictions, [1, 2, 3]))
  printTest("TestOuterMix1",ps,eps)


def testMakeSymDirMult1(N):
  sivm = SIVM()
  sivm.assume("f", "(make_sym_dir_mult 1.0 2)")
  sivm.predict("(f)")
  predictions = loggingInfer(sivm,2,N)
  ps = [.5, .5]
  eps = normalizeList(countPredictions(predictions, [0,1]))
  printTest("TestMakeSymDirMult1",ps,eps)


def testMakeSymDirMult2(N):
  sivm = SIVM()
  sivm.assume("a", "(normal 10.0 1.0)")
  sivm.assume("f", "(make_sym_dir_mult a 4)")
  sivm.predict("(f)")
  
  for i in range(1,4):
    for j in range(20):
      sivm.observe("(f)", "atom<%d>" % i)

  predictions = loggingInfer(sivm,3,N)
  ps = [.1,.3,.3,.3]
  eps = normalizeList(countPredictions(predictions, [0,1,2,3]))
  printTest("TestMakeSymDirMult2",ps,eps)


def testMakeUCSymDirMult1(N):
  sivm = SIVM()
  sivm.assume("a", "(normal 10.0 1.0)")
  sivm.assume("f", "(make_uc_sym_dir_mult a 4)")
  sivm.predict("(f)")

  for i in range(1,4):
    for j in range(20):
      sivm.observe("(f)", "atom<%d>" % i)

  predictions = loggingInfer(sivm,3,N)
  ps = [.1,.3,.3,.3]
  eps = normalizeList(countPredictions(predictions, [0,1,2,3]))
  printTest("TestMakeUCSymDirMult1",ps,eps)


def testLazyHMM1(N):
  N = N
  sivm = SIVM()
  sivm.assume("f","""
(mem 
(lambda (i) 
  (branch (eq i 0) 
     (lambda () (bernoulli 0.5))
     (lambda () (branch (f (minus i 1))
                 (lambda () (bernoulli 0.7))
                 (lambda () (bernoulli 0.3)))))))
""")

  sivm.assume("g","""
(mem (lambda (i)
  (branch (f i)
     (lambda () (bernoulli 0.8))
     (lambda () (bernoulli 0.1)))))
""")

  sivm.observe("(g 1)",False)
  sivm.observe("(g 2)",False)
  sivm.observe("(g 3)",True)
  sivm.observe("(g 4)",False)
  sivm.observe("(g 5)",False)
  sivm.predict("(f 0)")
  sivm.predict("(f 1)")
  sivm.predict("(f 2)")
  sivm.predict("(f 3)")
  sivm.predict("(f 4)")
  sivm.predict("(f 5)")

  n = 6
  sums = [0 for i in range(n)]

  for t in range(N):
      # TODO make this pgibbs with global drg
    sivm.infer(10, kernel="mh", use_global_scaffold=False)
    for i in range(n):
      sums[i] += sivm.report(8 + i)

  ps = [.3531,.1327,.1796,.6925,.1796,.1327]
  eps = [float(x) / N for x in sums] if N > 0 else [0 for x in sums]
  printTest("testLazyHMM1 (mixes terribly)",ps,eps)

def testLazyHMMSP1(N):
  sivm = SIVM()
  sivm.assume("f","""
(make_lazy_hmm 
  (make_vector 0.5 0.5)
  (make_vector 
    (make_vector 0.7 0.3)
    (make_vector 0.3 0.7))
  (make_vector
    (make_vector 0.9 0.2)
    (make_vector 0.1 0.8)))
""");
  sivm.observe("(f 1)","atom<0>")
  sivm.observe("(f 2)","atom<0>")
  sivm.observe("(f 3)","atom<1>")
  sivm.observe("(f 4)","atom<0>")
  sivm.observe("(f 5)","atom<0>")
  sivm.predict("(f 6)")

  predictions = loggingInfer(sivm,7,N)
  ps = [0.6528, 0.3472]
  eps = normalizeList(countPredictions(predictions,[0,1]))
  printTest("testLazyHMMSP1",ps,eps)

def testStaleAAA1(N):
  sivm = SIVM()
  sivm.assume("a", "1.0")
  sivm.assume("f", "(make_uc_sym_dir_mult a 2)")
  sivm.assume("g", "(mem f)")
  sivm.assume("h", "g")
  sivm.predict("(h)")

  for i in range(9):
    sivm.observe("(f)", "atom<1>")

  predictions = loggingInfer(sivm,5,N)
  ps = [.9, .1]
  eps = normalizeList(countPredictions(predictions, [1, 0]))
  printTest("TestStaleAAA1",ps,eps)

def testStaleAAA2(N):
  sivm = SIVM()
  sivm.assume("a", "1.0")
  sivm.assume("f", "(make_uc_sym_dir_mult a 2)")
  sivm.assume("g", "(lambda () f)")
  sivm.assume("h", "(g)")
  sivm.predict("(h)")

  for i in range(9):
    sivm.observe("(f)", "atom<1>")

  predictions = loggingInfer(sivm,5,N)
  ps = [.9, .1]
  eps = normalizeList(countPredictions(predictions, [1, 0]))
  printTest("TestStaleAAA2",ps,eps)

def testMap1(N):
  sivm = SIVM()
  sivm.assume("x","(bernoulli 1.0)")
  sivm.assume("m","""(make_map (list (quote x) (quote y))
                               (list (normal 0.0 1.0) (normal 10.0 1.0)))""")
  sivm.predict("""(normal (plus 
                           (map_lookup m (quote x))
                           (map_lookup m (quote y))
                           (map_lookup m (quote y)))
                         1.0)""")

  predictions = loggingInfer(sivm,3,N)
  mean = float(sum(predictions))/len(predictions) if len(predictions) > 0 else 0
  print "---TestMap1---"
  print "(20.0," + str(mean) + ")"


def testEval1(N):
  sivm = SIVM()
  sivm.assume("globalEnv","(get_current_environment)")
  sivm.assume("exp","(quote (bernoulli 0.7))")
  sivm.predict("(eval exp globalEnv)")

  predictions = loggingInfer(sivm,3,N)
  ps = [.7, .3]
  eps = normalizeList(countPredictions(predictions, [1, 0]))
  printTest("TestEval1",ps,eps)

def testEval2(N):
  sivm = SIVM()
  sivm.assume("p","(uniform_continuous 0.0 1.0)")
  sivm.assume("globalEnv","(get_current_environment)")
  sivm.assume("exp","""(quote 
  (branch (bernoulli p) 
        (lambda () (normal 10.0 1.0))
        (lambda () (normal 0.0 1.0)))
)""")
  
  sivm.assume("x","(eval exp globalEnv)")
  sivm.observe("x",11.0)

  predictions = loggingInfer(sivm,1,N)
  mean = float(sum(predictions))/len(predictions) if len(predictions) > 0 else 0
  print "---TestEval2---"
  print "(0.667," + str(mean) + ")"

def testEval3(N):
  sivm = SIVM()
  sivm.assume("p","(uniform_continuous 0.0 1.0)")
  sivm.assume("globalEnv","(get_current_environment)")
  sivm.assume("exp","""(quote 
  (branch ((lambda () (bernoulli p)))
        (lambda () ((lambda () (normal 10.0 1.0))))
        (lambda () (normal 0.0 1.0)))
)""")
  
  sivm.assume("x","(eval exp globalEnv)")
  sivm.observe("x",11.0)

  predictions = loggingInfer(sivm,1,N)
  mean = float(sum(predictions))/len(predictions) if len(predictions) > 0 else 0
  print "---TestEval3---"
  print "(0.667," + str(mean) + ")"

def testApply1(N):
  sivm = SIVM()
  sivm.assume("apply","(lambda (op args) (eval (pair op args) (get_empty_environment)))")
  sivm.predict("(apply times (list (normal 10.0 1.0) (normal 10.0 1.0) (normal 10.0 1.0)))")

  predictions = loggingInfer(sivm,2,N)
  mean = float(sum(predictions))/len(predictions) if len(predictions) > 0 else 0
  print "---TestApply1---"
  print "(1000ish," + str(mean) + ")"


def testExtendEnv1(N):
  sivm = SIVM()
  sivm.assume("env1","(get_current_environment)")
  
  sivm.assume("env2","(extend_environment env1 (quote x) (normal 0.0 1.0))")
  sivm.assume("env3","(extend_environment env2 (quote x) (normal 10.0 1.0))")
  sivm.assume("exp","(quote (normal x 1.0))")
  sivm.predict("(normal (eval exp env3) 1.0)")

  predictions = loggingInfer(sivm,5,N)
  mean = float(sum(predictions))/len(predictions) if len(predictions) > 0 else 0
  print "---TestExtendEnv1---"
  print "(10," + str(mean) + ")"



# TODO need extend_env, symbol?
def sivmWithSTDLIB(sivm):
  sivm.assume("make_ref","(lambda (x) (lambda () x))")
  sivm.assume("deref","(lambda (x) (x))")
  sivm.assume("venture_apply","(lambda (op args) (eval (pair op args) (get_empty_environment)))")
  sivm.assume("incremental_apply","""
(lambda (operator operands)
  (incremental_eval (deref (list_ref operator 3))

                    (extend_env env
				(deref (list_ref operator 2))
                                operands)))
""")
  sivm.assume("incremental_eval","""
(lambda (exp env)
  (branch 
    (is_symbol exp)
    (quote (eval exp env))
    (quote 
      (branch
        (not (is_pair exp))
        (quote exp)
        (branch 
          (sym_eq (deref (list_ref exp 0)) (quote lambda))
	  (quote (pair env (rest exp)))
          (quote 
            ((lambda (operator operands)
               (branch 
                 (is_pair operator)
                 (quote (incremental_apply operator operands))
                 (quote (venture_apply operator operands))))
             (incremental_eval (deref (first exp)) env)
             (map_list (lambda (x) (make_ref (incremental_eval (deref x) env))) (rest exp))))
)))))
""")
  return sivm

def testList1():
  sivm = SIVM()
  sivm.assume("x1","(list)")
  sivm.assume("x2","(pair 1.0 x1)")
  sivm.assume("x3","(pair 2.0 x2)")
  sivm.assume("x4","(pair 3.0 x3)")
  sivm.assume("f","(lambda (x) (times x x x))")
  sivm.assume("y4","(map_list f x4)")

  y4 = sivm.predict("(first y4)")
  y3 = sivm.predict("(list_ref y4 1)")
  y2 = sivm.predict("(list_ref (rest y4) 1)")
  px1 = sivm.predict("(is_pair x1)")
  px4 = sivm.predict("(is_pair x4)")
  py4 = sivm.predict("(is_pair y4)")

  assert(sivm.report(7) == 27.0);
  assert(sivm.report(8) == 8.0);
  assert(sivm.report(9) == 1.0);

  assert(not sivm.report(10));
  assert(sivm.report(11));
  assert(sivm.report(11));

  print "Passed TestList1()"

def loadPYMem(sivm):
  sivm.assume("pick_a_stick","""
(lambda (sticks k)
  (branch (bernoulli (sticks k))
          (lambda () k)
          (lambda () (pick_a_stick sticks (plus k 1)))))
""")
  
  sivm.assume("make_sticks","""
(lambda (alpha d)
  ((lambda (sticks) (lambda () (pick_a_stick sticks 1)))
   (mem
    (lambda (k)
      (beta (minus 1 d)
            (plus alpha (times k d)))))))
""")

  sivm.assume("u_pymem","""
(lambda (alpha d base_dist)
  ((lambda (augmented_proc py)
     (lambda () (augmented_proc (py))))
   (mem (lambda (stick_index) (base_dist)))
   (make_sticks alpha d)))
""")

  sivm.assume("pymem","""
(lambda (alpha d base_dist)
  ((lambda (augmented_proc crp)
     (lambda () (augmented_proc (crp))))
   (mem (lambda (table) (base_dist)))
   (make_crp alpha d)))
""")

def testDPMem1(N):
  sivm = SIVM()
  loadPYMem(sivm)
  sivm.assume("dpmem","""
(lambda (alpha base_dist)
  ((lambda (augmented_proc crp)
     (lambda () (augmented_proc (crp))))
   (mem (lambda (table) (base_dist)))
   (make_crp alpha)))
""")
  sivm.assume("alpha","(uniform_continuous 0.1 20.0)")
  sivm.assume("base_dist","(lambda () (real (categorical 0.5 0.5)))")
  sivm.assume("f","(dpmem alpha base_dist)")

  sivm.predict("(f)")
  sivm.predict("(f)")
  sivm.observe("(normal (f) 1.0)",1.0)
  sivm.observe("(normal (f) 1.0)",1.0)
  sivm.observe("(normal (f) 1.0)",0.0)
  sivm.observe("(normal (f) 1.0)",0.0)
  sivm.infer(N)

def observeCategories(sivm,counts):
  for i in range(len(counts)):
    for ct in range(counts[i]):
      sivm.observe("(normal (f) 1.0)",i)

def testCRP1(N,isCollapsed):
  sivm = SIVM()
  loadPYMem(sivm)
  sivm.assume("alpha","(gamma 1.0 1.0)")
  sivm.assume("d","(uniform_continuous 0.0 0.1)")
  sivm.assume("base_dist","(lambda () (real (categorical 0.2 0.2 0.2 0.2 0.2)))")
  if isCollapsed: sivm.assume("f","(pymem alpha d base_dist)")
  else: sivm.assume("f","(u_pymem alpha d base_dist)")
    
  sivm.predict("(f)",label="pid")

  observeCategories(sivm,[2,2,5,1,0])

  predictions = loggingInfer(sivm,"pid",N)
  ps = normalizeList([3,3,6,2,1])
  eps = normalizeList(countPredictions(predictions, [0,1,2,3,4]))
  printTest("TestCRP1 (not exact)",ps,eps)

def loadHPY(sivm,topCollapsed,botCollapsed):
  loadPYMem(sivm)
  sivm.assume("alpha","(gamma 1.0 1.0)")
  sivm.assume("d","(uniform_continuous 0.0 0.1)")
  sivm.assume("base_dist","(lambda () (real (categorical 0.2 0.2 0.2 0.2 0.2)))")
  if topCollapsed: sivm.assume("intermediate_dist","(pymem alpha d base_dist)")
  else: sivm.assume("intermediate_dist","(u_pymem alpha d base_dist)")
  if botCollapsed: sivm.assume("f","(pymem alpha d intermediate_dist)")
  else: sivm.assume("f","(u_pymem alpha d intermediate_dist)")

def predictHPY(N,topCollapsed,botCollapsed):
  sivm = SIVM()
  loadHPY(sivm,topCollapsed,botCollapsed)
  sivm.predict("(f)",label="pid")
  observeCategories(sivm,[2,2,5,1,0])
  return loggingInfer(sivm,"pid",N)

def testHPYMem1(N):
  print "---TestHPYMem1---"
  for top in [False,True]:
    for bot in [False,True]:
      attempt = normalizeList(countPredictions(predictHPY(N,top,bot), [0,1,2,3,4]))
      print("(%s,%s): %s" % (top,bot,attempt))

def testGeometric1(N):
  sivm = SIVM()
  sivm.assume("alpha1","(gamma 5.0 2.0)")
  sivm.assume("alpha2","(gamma 5.0 2.0)")
  sivm.assume("p", "(beta alpha1 alpha2)")
  sivm.assume("geo","(lambda (p) (branch (bernoulli p) (lambda () 1) (lambda () (plus 1 (geo p)))))")
  sivm.predict("(geo p)",label="pid")
  
  predictions = loggingInfer(sivm,"pid",N)

  k = 7
  ps = [math.pow(2,-n) for n in range(1,k)]
  eps = normalizeList(countPredictions(predictions, range(1,k)))
  printTest("TestGeometric1",ps,eps)


def testTrig1(N):
  sivm = SIVM()
  sivm.assume("sq","(lambda (x) (* x x))")
  sivm.assume("x","(normal 0.0 1.0)")
  sivm.assume("a","(sq (sin x))")
  sivm.assume("b","(sq (cos x))")
  sivm.predict("(+ a b)")
  for i in range(N/10):
    sivm.infer({"kernel":"mh","transitions":10,"use_global_scaffold":False})
    assert abs(sivm.report(5) - 1) < .001
  print "Passed TestTrig1()"

def testForget1():
  sivm = SIVM()

  sivm.assume("x","(normal 0.0 1.0)")
  sivm.assume("f","(lambda (y) (normal y 1.0))")
  sivm.assume("g","(lambda (z) (normal z 2.0))")

  sivm.predict("(f 1.0)",label="id1")
  sivm.observe("(g 2.0)",3.0,label="id2")
  sivm.observe("(g 3.0)",3.0,label="id3")
  
  sivm.forget("id3")
  sivm.forget("id2")
  sivm.forget("id1")

def testForget2():
  sivm = SIVM()

  sivm.assume("x","(normal 0.0 1.0)")
  sivm.assume("f","(lambda (y) (normal y 1.0))")
  sivm.assume("g","(lambda (z) (normal z 2.0))")

  sivm.predict("(f 1.0)",label="id1")
  sivm.observe("(g 2.0)",3.0,label="id2")
  sivm.observe("(g 3.0)",3.0,label="id3")
  
  sivm.forget("id1")
  sivm.forget("id2")
  sivm.forget("id3")
