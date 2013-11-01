from sivm import SIVM
import math
import pdb

def normalizeList(seq): 
  denom = sum(seq)
  if denom > 0: return [ float(x)/denom for x in seq]
  else: return [0 for x in seq]

def countPredictions(predictions, seq):
  return [predictions.count(x) for x in seq]

def totalDifference(eps,ops): return sum([ math.pow(x - y,2) for (x,y) in zip(eps,ops)])
    
def printTest(testName,eps,ops):
  print "---Test: " + testName + "---"
  print "Expected: " + str(eps)
  print "Observed: " + str(ops)
  print "Total Difference: " + str(totalDifference(eps,ops))

def loggingInfer(sivm,address,T):
  predictions = []
  for t in range(T):
    sivm.infer(1)
    predictions.append(sivm.trace.extractValue(address))
  return predictions

def runTests(N):
  testBernoulli1(N)
  testMHNormal1(N)
  testMem1(N)
  testMem2(N)
  testMem3(N)
  testSprinkler1(N)
  testSprinkler2(N)
  testMHHMM1(N)
  testOuterMix1(N)
  testMakeSymDirMult1(N)
  testMakeSymDirMult2(N)
  testMakeUCSymDirMult1(N)
  testLazyHMM1(N)
  testStaleAAA1(N)
  testStaleAAA2(N)
# testGeometric1(N)

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

  

def testMHNormal1(N):
  sivm = SIVM()
  sivm.assume("a", "(normal 10.0 1.0)")
  sivm.assume("b", "(normal a 1.0)")
  sivm.observe("((lambda () (normal b 1.0))))", 14.0)
  sivm.predict("""
(branch (real_lt a 100.0) 
        (lambda () (normal (real_plus a b) 1.0))
        (lambda () (normal (real_times a b) 1.0)))
""")

  predictions = loggingInfer(sivm,4,N)
  mean = float(sum(predictions))/len(predictions) if len(predictions) > 0 else 0
  print "---TestMHNormal1---"
  print "(23.9," + str(mean) + ")"

def testMem0(N):
  sivm = SIVM()
  sivm.assume("f","(mem (lambda (x) (bernoulli x)))")
  sivm.predict("(f 0.5)")
  sivm.predict("(f 0.5)")
  sivm.infer(N)


def testMem1(N):
  sivm = SIVM()
  sivm.assume("f","(mem (lambda (arg) (int_plus 1 (categorical (make_vector 0.4 0.6)))))")
  sivm.assume("x","(f 1)")
  sivm.assume("y","(f 1)")
  sivm.assume("w","(f 2)")
  sivm.assume("z","(f 2)")
  sivm.assume("q","(int_plus 1 (categorical (make_vector 0.1 0.9)))")
  sivm.predict('(int_plus x (int_plus y (int_plus w (int_plus z q))))');

  predictions = loggingInfer(sivm,7,N)
  ps = [0.4 * 0.4 * 0.1, 0.6 * 0.6 * 0.9]
  eps = [ float(x) / N for x in countPredictions(predictions, [5,10])] if N > 0 else [0,0]
  printTest("TestMem1",ps,eps)

def testMem2(N):
  sivm = SIVM()
  sivm.assume("f","(mem (lambda (arg) (int_plus 1 (categorical (make_vector 0.4 0.6)))))")
  sivm.assume("g","((lambda () (mem (lambda (y) (f (int_plus y 1))))))")
  sivm.assume("x","(f ((branch (bernoulli 0.5) (lambda () (lambda () 1)) (lambda () (lambda () 1)))))")
  sivm.assume("y","(g ((lambda () 0)))")
  sivm.assume("w","((lambda () (f 2)))")
  sivm.assume("z","(g 1)")
  sivm.assume("q","(int_plus 1 (categorical (make_vector 0.1 0.9)))")
  sivm.predict('(int_plus x (int_plus y (int_plus w (int_plus z q))))');

  predictions = loggingInfer(sivm,8,N)
  ps = [0.4 * 0.4 * 0.1, 0.6 * 0.6 * 0.9]
  eps = [ float(x) / N for x in countPredictions(predictions, [5,10])] if N > 0 else [0,0]
  printTest("TestMem2",ps,eps)

def testMem3(N):
  sivm = SIVM()
  sivm.assume("f","(mem (lambda (arg) (int_plus 1 (categorical (make_vector 0.4 0.6)))))")
  sivm.assume("g","((lambda () (mem (lambda (y) (f (int_plus y 1))))))")
  sivm.assume("x","(f ((lambda () 1)))")
  sivm.assume("y","(g ((lambda () (branch (bernoulli 1.0) (lambda () 0) (lambda () 100)))))")
  sivm.assume("w","((lambda () (f 2)))")
  sivm.assume("z","(g 1)")
  sivm.assume("q","(int_plus 1 (categorical (make_vector 0.1 0.9)))")
  sivm.predict('(int_plus x (int_plus y (int_plus w (int_plus z q))))');

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
  N = N * 4

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

def testIf1():
  sivm = SIVM()
  sivm.assume('IF', '(lambda () branch)')
  sivm.assume('IF?', '(branch (bernoulli 0.5) IF IF)')
  sivm.predict('(IF? (bernoulli 0.5) IF IF)')
  sivm.infer(N/10)

def testIf2(N):
  sivm = SIVM()
  sivm.assume('if1', '(branch (bernoulli 0.5) (lambda () branch) (lambda () branch))')
  sivm.assume('if2', '(branch (bernoulli 0.5) (lambda () if1) (lambda () if1))')
  sivm.assume('if3', '(branch (bernoulli 0.5) (lambda () if2) (lambda () if2))')
  sivm.assume('if4', '(branch (bernoulli 0.5) (lambda () if3) (lambda () if3))')
  sivm.infer(N/10)


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
(mem (lambda (i) (branch (int_eq i 0) (lambda () (normal 0.0 1.0)) (lambda () (normal (f (int_minus i 1)) 1.0)))))
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

  sivm.observe("(f)",1)
  sivm.observe("(f)",1)
  sivm.observe("(f)",1)
  sivm.observe("(f)",1)
  sivm.observe("(f)",1)

  sivm.observe("(f)",1)
  sivm.observe("(f)",1)
  sivm.observe("(f)",1)
  sivm.observe("(f)",1)
  sivm.observe("(f)",1)

  sivm.observe("(f)",1)
  sivm.observe("(f)",1)
  sivm.observe("(f)",1)
  sivm.observe("(f)",1)
  sivm.observe("(f)",1)

  sivm.observe("(f)",1)
  sivm.observe("(f)",1)
  sivm.observe("(f)",1)
  sivm.observe("(f)",1)
  sivm.observe("(f)",1)

  sivm.observe("(f)",2)
  sivm.observe("(f)",2)
  sivm.observe("(f)",2)
  sivm.observe("(f)",2)
  sivm.observe("(f)",2)

  sivm.observe("(f)",2)
  sivm.observe("(f)",2)
  sivm.observe("(f)",2)
  sivm.observe("(f)",2)
  sivm.observe("(f)",2)

  sivm.observe("(f)",2)
  sivm.observe("(f)",2)
  sivm.observe("(f)",2)
  sivm.observe("(f)",2)
  sivm.observe("(f)",2)

  sivm.observe("(f)",2)
  sivm.observe("(f)",2)
  sivm.observe("(f)",2)
  sivm.observe("(f)",2)
  sivm.observe("(f)",2)

  sivm.observe("(f)",3)
  sivm.observe("(f)",3)
  sivm.observe("(f)",3)
  sivm.observe("(f)",3)
  sivm.observe("(f)",3)

  sivm.observe("(f)",3)
  sivm.observe("(f)",3)
  sivm.observe("(f)",3)
  sivm.observe("(f)",3)
  sivm.observe("(f)",3)

  sivm.observe("(f)",3)
  sivm.observe("(f)",3)
  sivm.observe("(f)",3)
  sivm.observe("(f)",3)
  sivm.observe("(f)",3)

  sivm.observe("(f)",3)
  sivm.observe("(f)",3)
  sivm.observe("(f)",3)
  sivm.observe("(f)",3)
  sivm.observe("(f)",3)

  predictions = loggingInfer(sivm,3,N)
  ps = [.1,.3,.3,.3]
  eps = normalizeList(countPredictions(predictions, [0,1,2,3]))
  printTest("TestMakeSymDirMult2",ps,eps)

def testMakeUCSymDirMult1(N):
  sivm = SIVM()
  sivm.assume("a", "(normal 10.0 1.0)")
  sivm.assume("f", "(make_uc_sym_dir_mult a 4)")
  sivm.predict("(f)")

  sivm.observe("(f)",1)
  sivm.observe("(f)",1)
  sivm.observe("(f)",1)
  sivm.observe("(f)",1)
  sivm.observe("(f)",1)

  sivm.observe("(f)",1)
  sivm.observe("(f)",1)
  sivm.observe("(f)",1)
  sivm.observe("(f)",1)
  sivm.observe("(f)",1)

  sivm.observe("(f)",1)
  sivm.observe("(f)",1)
  sivm.observe("(f)",1)
  sivm.observe("(f)",1)
  sivm.observe("(f)",1)

  sivm.observe("(f)",1)
  sivm.observe("(f)",1)
  sivm.observe("(f)",1)
  sivm.observe("(f)",1)
  sivm.observe("(f)",1)

  sivm.observe("(f)",2)
  sivm.observe("(f)",2)
  sivm.observe("(f)",2)
  sivm.observe("(f)",2)
  sivm.observe("(f)",2)

  sivm.observe("(f)",2)
  sivm.observe("(f)",2)
  sivm.observe("(f)",2)
  sivm.observe("(f)",2)
  sivm.observe("(f)",2)

  sivm.observe("(f)",2)
  sivm.observe("(f)",2)
  sivm.observe("(f)",2)
  sivm.observe("(f)",2)
  sivm.observe("(f)",2)

  sivm.observe("(f)",2)
  sivm.observe("(f)",2)
  sivm.observe("(f)",2)
  sivm.observe("(f)",2)
  sivm.observe("(f)",2)

  sivm.observe("(f)",3)
  sivm.observe("(f)",3)
  sivm.observe("(f)",3)
  sivm.observe("(f)",3)
  sivm.observe("(f)",3)

  sivm.observe("(f)",3)
  sivm.observe("(f)",3)
  sivm.observe("(f)",3)
  sivm.observe("(f)",3)
  sivm.observe("(f)",3)

  sivm.observe("(f)",3)
  sivm.observe("(f)",3)
  sivm.observe("(f)",3)
  sivm.observe("(f)",3)
  sivm.observe("(f)",3)

  sivm.observe("(f)",3)
  sivm.observe("(f)",3)
  sivm.observe("(f)",3)
  sivm.observe("(f)",3)
  sivm.observe("(f)",3)

  predictions = loggingInfer(sivm,3,N)
  ps = [.1,.3,.3,.3]
  eps = normalizeList(countPredictions(predictions, [0,1,2,3]))
  printTest("TestMakeUCSymDirMult1",ps,eps)


def testLazyHMM1(N):
  N = N * 2
  sivm = SIVM()
  sivm.assume("f","""
(mem 
(lambda (i) 
  (branch (int_eq i 0) 
     (lambda () (bernoulli 0.5))
     (lambda () (branch (f (int_minus i 1))
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
    sivm.infer(1)
    for i in range(n):
      sums[i] += sivm.trace.extractValue(8 + i)

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
  sivm.observe("(f 1)",0)
  sivm.observe("(f 2)",0)
  sivm.observe("(f 3)",1)
  sivm.observe("(f 4)",0)
  sivm.observe("(f 5)",0)
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

  sivm.observe("(f)",1)
  sivm.observe("(f)",1)
  sivm.observe("(f)",1)
  sivm.observe("(f)",1)
  sivm.observe("(f)",1)

  sivm.observe("(f)",1)
  sivm.observe("(f)",1)
  sivm.observe("(f)",1)
  sivm.observe("(f)",1)


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

  sivm.observe("(f)",1)
  sivm.observe("(f)",1)
  sivm.observe("(f)",1)
  sivm.observe("(f)",1)
  sivm.observe("(f)",1)

  sivm.observe("(f)",1)
  sivm.observe("(f)",1)
  sivm.observe("(f)",1)
  sivm.observe("(f)",1)

  predictions = loggingInfer(sivm,5,N)
  ps = [.9, .1]
  eps = normalizeList(countPredictions(predictions, [1, 0]))
  printTest("TestStaleAAA2",ps,eps)














def testGeometric1(N):
  sivm = SIVM()
  sivm.assume("alpha1","(gamma 5.0 2.0)")
  sivm.assume("alpha2","(gamma 5.0 2.0)")
  sivm.assume("p", "(beta alpha1 alpha2)")
  sivm.assume("geo","(lambda (p) (branch (bernoulli p) (lambda () 1) (lambda () (int_plus 1 (geo p)))))")
  pID = sivm.predict("(geo p)")[0]
  
  predictions = loggingInfer(sivm,"5",N)

  k = 7
  ps = [math.pow(2,-n) for n in range(1,k)]
  eps = normalizeList(countPredictions(predictions, range(1,k)))
  printTest("TestGeometric1",ps,eps)
