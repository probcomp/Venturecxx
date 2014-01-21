




def testBlockingExample0(N):
  ripl = RIPL()
  ripl.assume("a", "(scope_include 0 0 (normal 10.0 1.0))")
  ripl.assume("b", "(scope_include 1 1 (normal a 1.0))")
  ripl.observe("(normal b 1.0)", 14.0)

  # If inference only frobnicates b, then the distribution on a
  # remains the prior.
  predictions = collectSamplesWith(ripl,1,N,{"transitions":10,"kernel":globalKernel,"scope":1,"block":1})
  cdf = stats.norm(loc=10.0, scale=1.0).cdf
  return reportKnownContinuous("testBlockingExample0", cdf, predictions, "N(10.0,1.0)")

def testBlockingExample1():
  ripl = RIPL()
  ripl.assume("a", "(scope_include 0 0 (normal 0.0 1.0))")
  ripl.assume("b", "(scope_include 0 0 (normal 1.0 1.0))")
  olda = ripl.report(1)
  oldb = ripl.report(2)
  # The point of block proposals is that both things change at once.
  ripl.sivm.core_sivm.engine.infer({"transitions":1, "kernel":globalKernel, "scope":0, "block":0})
  newa = ripl.report(1)
  newb = ripl.report(2)
  assert not(olda == newa)
  assert not(oldb == newb)
  return reportPassage("testBlockingExample1")

def testBlockingExample2():
  ripl = RIPL()
  ripl.assume("a", "(scope_include 0 0 (normal 0.0 1.0))")
  ripl.assume("b", "(scope_include 0 0 (normal 1.0 1.0))")
  ripl.assume("c", "(scope_include 0 1 (normal 2.0 1.0))")
  ripl.assume("d", "(scope_include 0 1 (normal 3.0 1.0))")
  olda = ripl.report(1)
  oldb = ripl.report(2)
  oldc = ripl.report(3)
  oldd = ripl.report(4)
  # Should change everything in one or the other block
  ripl.sivm.core_sivm.engine.infer({"transitions":1, "kernel":globalKernel, "scope":0, "block":"one"})
  newa = ripl.report(1)
  newb = ripl.report(2)
  newc = ripl.report(3)
  newd = ripl.report(4)
  if (olda == newa):
    assert oldb == newb
    assert not(oldc == newc)
    assert not(oldd == newd)
  else:
    assert not(oldb == newb)
    assert oldc == newc
    assert oldd == newd
  return reportPassage("testBlockingExample2")

def testBlockingExample3():
  ripl = RIPL()
  ripl.assume("a", "(scope_include 0 0 (normal 0.0 1.0))")
  ripl.assume("b", "(scope_include 0 1 (normal 1.0 1.0))")
  olda = ripl.report(1)
  oldb = ripl.report(2)
  # The point of block proposals is that both things change at once.
  ripl.sivm.core_sivm.engine.infer({"transitions":1, "kernel":globalKernel, "scope":0, "block":"all"})
  newa = ripl.report(1)
  newb = ripl.report(2)
  assert not(olda == newa)
  assert not(oldb == newb)
  return reportPassage("testBlockingExample3")



def testGamma1(N):
  ripl = RIPL()
  ripl.assume("a","(gamma 10.0 10.0)")
  ripl.assume("b","(gamma 10.0 10.0)")
  ripl.predict("(gamma a b)")

  predictions = collectSamples(ripl,3,N)
  # TODO What, actually, is the mean of (gamma (gamma 10 10) (gamma 10 10))?
  # It's pretty clear that it's not 1.
  return reportKnownMean("TestGamma1", 10/9.0, predictions)










def testList1():
  ripl = RIPL()
  ripl.assume("x1","(list)")
  ripl.assume("x2","(pair 1.0 x1)")
  ripl.assume("x3","(pair 2.0 x2)")
  ripl.assume("x4","(pair 3.0 x3)")
  ripl.assume("f","(lambda (x) (times x x x))")
  ripl.assume("y4","(map_list f x4)")

  y4 = ripl.predict("(first y4)")
  y3 = ripl.predict("(list_ref y4 1)")
  y2 = ripl.predict("(list_ref (rest y4) 1)")
  px1 = ripl.predict("(is_pair x1)")
  px4 = ripl.predict("(is_pair x4)")
  py4 = ripl.predict("(is_pair y4)")

  assert(ripl.report(7) == 27.0);
  assert(ripl.report(8) == 8.0);
  assert(ripl.report(9) == 1.0);

  assert(not ripl.report(10));
  assert(ripl.report(11));
  assert(ripl.report(11));

  return reportPassage("TestList1")

def loadPYMem(ripl):
  ripl.assume("pick_a_stick","""
(lambda (sticks k)
  (branch (bernoulli (sticks k))
    (lambda () k)
    (lambda () (pick_a_stick sticks (plus k 1)))))
""")

  ripl.assume("make_sticks","""
(lambda (alpha d)
  ((lambda (sticks) (lambda () (pick_a_stick sticks 1)))
   (mem (lambda (k)
     (beta (minus 1 d)
           (plus alpha (times k d)))))))
""")

  ripl.assume("u_pymem","""
(lambda (alpha d base_dist)
  ((lambda (augmented_proc py)
     (lambda () (augmented_proc (py))))
   (mem (lambda (stick_index) (base_dist)))
   (make_sticks alpha d)))
""")

  ripl.assume("pymem","""
(lambda (alpha d base_dist)
  ((lambda (augmented_proc crp)
     (lambda () (augmented_proc (crp))))
   (mem (lambda (table) (base_dist)))
   (make_crp alpha d)))
""")

def loadDPMem(ripl):
  ripl.assume("pick_a_stick","""
(lambda (sticks k)
  (if (bernoulli (sticks k))
      k
      (pick_a_stick sticks (plus k 1))))
""")

  ripl.assume("make_sticks","""
(lambda (alpha)
  ((lambda (sticks) (lambda () (pick_a_stick sticks 1)))
   (mem (lambda (k)
     (beta 1 alpha)))))
""")

  ripl.assume("u_dpmem","""
(lambda (alpha base_dist)
  ((lambda (augmented_proc py)
     (lambda () (augmented_proc (py))))
   (mem (lambda (stick_index) (base_dist)))
   (make_sticks alpha)))
""")


def testDPMem1(N):
  ripl = RIPL()
  loadDPMem(ripl)

  ripl.assume("alpha","(uniform_continuous 0.1 20.0)")
  ripl.assume("base_dist","(lambda () (real (categorical 0.5 0.5)))")
  ripl.assume("f","(u_dpmem alpha base_dist)")

  ripl.predict("(f)")
  ripl.predict("(f)")
  ripl.observe("(normal (f) 1.0)",1.0)
  ripl.observe("(normal (f) 1.0)",1.0)
  ripl.observe("(normal (f) 1.0)",0.0)
  ripl.observe("(normal (f) 1.0)",0.0)
  ripl.infer(N)
  return reportPassage("TestDPMem1")

def observeCategories(ripl,counts):
  for i in range(len(counts)):
    for ct in range(counts[i]):
      ripl.observe("(flip (if (= (f) %d) 1.0 0.1))" % i,"true")

def testCRP1(N,isCollapsed):
  ripl = RIPL()
  loadPYMem(ripl)
  ripl.assume("alpha","(gamma 1.0 1.0)")
  ripl.assume("d","(uniform_continuous 0.0 0.1)")
  ripl.assume("base_dist","(lambda () (real (categorical 0.2 0.2 0.2 0.2 0.2)))")
  if isCollapsed: ripl.assume("f","(pymem alpha d base_dist)")
  else: ripl.assume("f","(u_pymem alpha d base_dist)")

  ripl.predict("(f)",label="pid")

  observeCategories(ripl,[2,2,5,1,0])

  predictions = collectSamples(ripl,"pid",N)
  ans = [(0,3), (1,3), (2,6), (3,2), (4,1)]
  return reportKnownDiscrete("TestCRP1 (not exact)", ans, predictions)

def loadHPY(ripl,topCollapsed,botCollapsed):
  loadPYMem(ripl)
  ripl.assume("alpha","(gamma 1.0 1.0)")
  ripl.assume("d","(uniform_continuous 0.0 0.1)")
  ripl.assume("base_dist","(lambda () (real (categorical 0.2 0.2 0.2 0.2 0.2)))")
  if topCollapsed: ripl.assume("intermediate_dist","(pymem alpha d base_dist)")
  else: ripl.assume("intermediate_dist","(u_pymem alpha d base_dist)")
  if botCollapsed: ripl.assume("f","(pymem alpha d intermediate_dist)")
  else: ripl.assume("f","(u_pymem alpha d intermediate_dist)")

def loadPY(ripl):
  loadPYMem(ripl)
  ripl.assume("alpha","(gamma 1.0 1.0)")
  ripl.assume("d","(uniform_continuous 0 0.0001)")
  ripl.assume("base_dist","(lambda () (real (categorical 0.2 0.2 0.2 0.2 0.2)))")
  ripl.assume("f","(u_pymem alpha d base_dist)")

def predictPY(N):
  ripl = RIPL()
  loadPY(ripl)
  ripl.predict("(f)",label="pid")
  observeCategories(ripl,[2,2,5,1,0])
  return collectSamples(ripl,"pid",N)

def predictHPY(N,topCollapsed,botCollapsed):
  ripl = RIPL()
  loadHPY(ripl,topCollapsed,botCollapsed)
  ripl.predict("(f)",label="pid")
  observeCategories(ripl,[2,2,5,1,0])
  return collectSamples(ripl,"pid",N)

def doTestHPYMem1(N):
  data = [countPredictions(predictHPY(N,top,bot), [0,1,2,3,4]) for top in [True,False] for bot in [True,False]]
  (chisq, pval) = stats.chi2_contingency(data)
  report = [
    "Expected: Samples from four equal distributions",
    "Observed:"]
  i = 0
  for top in ["Collapsed", "Uncollapsed"]:
    for bot in ["Collapsed", "Uncollapsed"]:
      report += "  (%s, %s): %s" % (top, bot, data[i])
      i += 1
  report += [
    "Chi^2   : " + str(chisq),
    "P value : " + str(pval)]
  return TestResult("TestHPYMem1", pval, "\n".join(report))

def testHPYMem1(N):
  if hasattr(stats, 'chi2_contingency'):
    return doTestHPYMem1(N)
  else:
    print "---TestHPYMem1 skipped for lack of scipy.stats.chi2_contingency"
    return reportPassage("TestHPYMem1")

def testGeometric1(N):
  ripl = RIPL()
  ripl.assume("alpha1","(gamma 5.0 2.0)")
  ripl.assume("alpha2","(gamma 5.0 2.0)")
  ripl.assume("p", "(beta alpha1 alpha2)")
  ripl.assume("geo","(lambda (p) (branch (bernoulli p) (lambda () 1) (lambda () (plus 1 (geo p)))))")
  ripl.predict("(geo p)",label="pid")

  predictions = collectSamples(ripl,"pid",N)

  k = 128
  ans = [(n,math.pow(2,-n)) for n in range(1,k)]
  return reportKnownDiscrete("TestGeometric1", ans, predictions)

def testTrig1(N):
  ripl = RIPL()
  ripl.assume("sq","(lambda (x) (* x x))")
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("a","(sq (sin x))")
  ripl.assume("b","(sq (cos x))")
  ripl.predict("(+ a b)")
  for i in range(N/10):
    ripl.infer(10)
    assert abs(ripl.report(5) - 1) < .001
  return reportPassage("TestTrig1")

def testForget1():
  ripl = RIPL()

  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("f","(lambda (y) (normal y 1.0))")
  ripl.assume("g","(lambda (z) (normal z 2.0))")

  ripl.predict("(f 1.0)",label="id1")
  ripl.observe("(g 2.0)",3.0,label="id2")
  ripl.observe("(g 3.0)",3.0,label="id3")

  ripl.forget("id1")
  ripl.forget("id2")
  ripl.forget("id3")

  real_sivm = ripl.sivm.core_sivm.engine
  assert real_sivm.get_entropy_info()["unconstrained_random_choices"] == 1
  assert real_sivm.logscore() < 0
  return reportPassage("TestForget1")

# This is the original one that fires an assert, when the (flip) has 0.0 or 1.0 it doesn't fail
def testReferences1(N):
  ripl = RIPL()
  ripl.assume("draw_type1", "(make_crp 1.0)")
  ripl.assume("draw_type0", "(if (flip) draw_type1 (lambda () 1))")
  ripl.assume("draw_type2", "(make_dir_mult 1 1)")
  ripl.assume("class", "(if (flip) (lambda (name) (draw_type0)) (lambda (name) (draw_type2)))")
  ripl.predict("(class 1)")
  ripl.predict("(flip)")
  # TODO What is trying to test?  The address in the logging infer refers to the bare (flip).
  predictions = collectSamples(ripl,6,N)
  ans = [(True,0.5), (False,0.5)]
  return reportKnownDiscrete("TestReferences1", ans, predictions)

#
def testReferences2(N):
  ripl = RIPL()
  ripl.assume("f", "(if (flip 0.5) (make_dir_mult 1 1) (lambda () 1))")
  ripl.predict("(f)")
#  ripl.predict("(flip)",label="pid")

  predictions = collectSamples(ripl,2,N)
  ans = [(True,0.75), (False,0.25)]
  return reportKnownDiscrete("TestReferences2", ans, predictions)

def testMemoizingOnAList():
  ripl = RIPL()
  ripl.assume("G","(mem (lambda (x) 1))")
  ripl.predict("(G (list 0))")
  predictions = collectSamples(ripl,2,1)
  assert predictions == [1]
  return reportPassage("TestMemoizingOnAList")

def testOperatorChanging(N):
  ripl = RIPL()
  ripl.assume("f","(mem (lambda () (flip)))")
  ripl.assume("op1","(if (flip) flip (lambda () (f)))")
  ripl.assume("op2","(if (op1) op1 (lambda () (op1)))")
  ripl.assume("op3","(if (op2) op2 (lambda () (op2)))")
  ripl.assume("op4","(if (op3) op2 op1)")
  ripl.predict("(op4)")
  ripl.observe("(op4)",True)
  predictions = collectSamples(ripl,6,N,kernel="mh")
  ans = [(True,0.75), (False,0.25)]
  return reportKnownDiscrete("TestOperatorChanging", ans, predictions)

def testObserveAPredict0(N):
  ripl = RIPL()
  ripl.assume("f","(if (flip) (lambda () (flip)) (lambda () (flip)))")
  ripl.predict("(f)")
  ripl.observe("(f)","true")
  ripl.predict("(f)")
  predictions = collectSamples(ripl,2,N)
  ans = [(True,0.5), (False,0.5)]
  return reportKnownDiscrete("TestObserveAPredict0", ans, predictions)


### These tests are illegal Venture programs, and cause PGibbs to fail because
# when we detach for one slice, a node may think it owns its value, but then
# when we constrain we reclaim it and delete it, so it ends up getting deleted
# twice.

# def testObserveAPredict1(N):
#   ripl = RIPL()
#   ripl.assume("f","(if (flip 0.0) (lambda () (flip)) (mem (lambda () (flip))))")
#   ripl.predict("(f)")
#   ripl.observe("(f)","true")
#   ripl.predict("(f)")
#   predictions = collectSamples(ripl,2,N)
#   ans = [(True,0.75), (False,0.25)]
#   return reportKnownDiscrete("TestObserveAPredict1", ans, predictions)


# def testObserveAPredict2(N):
#   ripl = RIPL()
#   ripl.assume("f","(if (flip) (lambda () (normal 0.0 1.0)) (mem (lambda () (normal 0.0 1.0))))")
#   ripl.observe("(f)","1.0")
#   ripl.predict("(* (f) 100)")
#   predictions = collectSamples(ripl,3,N)
#   mean = float(sum(predictions))/len(predictions) if len(predictions) > 0 else 0
#   print "---TestObserveAPredict2---"
#   print "(25," + str(mean) + ")"
#   print "(note: true answer is 50, but program is illegal and staleness is correct behavior)"


def testBreakMem(N):
  ripl = RIPL()
  ripl.assume("pick_a_stick","""
(lambda (sticks k)
  (if (bernoulli (sticks k))
      k
      (pick_a_stick sticks (plus k 1))))
""")
  ripl.assume("d","(uniform_continuous 0.4 0.41)")

  ripl.assume("f","(mem (lambda (k) (beta 1.0 (times k d))))")
  ripl.assume("g","(lambda () (pick_a_stick f 1))")
  ripl.predict("(g)")
  ripl.infer(N)
  return reportPassage("TestBreakMem")

def testHPYLanguageModel1(N):
  ripl = RIPL()
  loadPYMem(ripl)

  # 5 letters for now
  ripl.assume("G_init","(make_sym_dir_mult 0.5 5)")

  # globally shared parameters for now
  ripl.assume("alpha","(gamma 1.0 1.0)")
  ripl.assume("d","(uniform_continuous 0.0 0.01)")

  # G(letter1 letter2 letter3) ~ pymem(alpha,d,G(letter2 letter3))
  ripl.assume("H","(mem (lambda (a) (pymem alpha d G_init)))")

  ripl.assume("noisy_true","(lambda (pred noise) (flip (if pred 1.0 noise)))")

  atoms = [0, 1, 2, 3, 4] * 4;

  for i in range(1,len(atoms)):
    ripl.observe("""
(noisy_true
  (atom_eq
    ((H atom<%d>))
    atom<%d>)
  0.001)
""" % (atoms[i-1],atoms[i]), "true")

  ripl.predict("((H atom<0>))",label="pid")

  predictions = collectSamples(ripl,"pid",N)
  ans = [(0,0.03), (1,0.88), (2,0.03), (3,0.03), (4,0.03)]
  return reportKnownDiscrete("testHPYLanguageModel1 (approximate)", ans, predictions)

def testHPYLanguageModel2(N):
  ripl = RIPL()
  loadPYMem(ripl)

  # 5 letters for now
  ripl.assume("G_init","(make_sym_dir_mult 0.5 5)")

  # globally shared parameters for now
  ripl.assume("alpha","(gamma 1.0 1.0)")
  ripl.assume("d","(uniform_continuous 0.0 0.01)")

  # G(letter1 letter2 letter3) ~ pymem(alpha,d,G(letter2 letter3))
  ripl.assume("G","""
(mem (lambda (context)
  (if (is_pair context)
      (pymem alpha d (G (rest context)))
      (pymem alpha d G_init))))
""")

  ripl.assume("noisy_true","(lambda (pred noise) (flip (if pred 1.0 noise)))")

  atoms = [0, 1, 2, 3, 4] * 4;

  for i in range(1,len(atoms)):
    ripl.observe("""
(noisy_true
  (atom_eq
    ((G (list atom<%d>)))
    atom<%d>)
  0.001)
""" % (atoms[i-1],atoms[i]), "true")

  ripl.predict("((G (list atom<0>)))",label="pid")

  predictions = collectSamples(ripl,"pid",N)
  ans = [(0,0.03), (1,0.88), (2,0.03), (3,0.03), (4,0.03)]
  return reportKnownDiscrete("testHPYLanguageModel2 (approximate)", ans, predictions)

def testGoldwater1(N):
  v = RIPL()

  #brent = open("brent_ratner/br-phono.txt", "r").readlines()
  #brent = [b.strip().split() for b in brent]
  #brent = ["".join(i) for i in brent]
  #brent = ["aaa", "bbb", "aaa", "bbb"]
  #brent = brent[:2]
  #brent = "".join(brent)
#  brent = ["catanddog", "dogandcat", "birdandcat","dogandbird","birdcatdog"]
  brent = ["aba","ab"]

  iterations = 100
  parameter_for_dirichlet = 1
#  n = 2 #eventually implement option to set n
  alphabet = "".join(set("".join(list(itertools.chain.from_iterable(brent)))))
  d = {}
  for i in xrange(len(alphabet)): d[alphabet[i]] = i

  v.assume("parameter_for_dirichlet", str(parameter_for_dirichlet))
  v.assume("alphabet_length", str(len(alphabet)))

  v.assume("sample_phone", "(make_sym_dir_mult parameter_for_dirichlet alphabet_length)")
  v.assume("sample_word_id", "(make_crp 1.0)")

  v.assume("sample_letter_in_word", """
(mem (lambda (word_id pos)
  (sample_phone)))
""")
#7
  v.assume("is_end", """
(mem (lambda (word_id pos)
  (flip .3)))
""")

  v.assume("get_word_id","""
(mem (lambda (sentence sentence_pos)
  (branch (= sentence_pos 0)
    (lambda () (sample_word_id))
    (lambda ()
      (branch (is_end (get_word_id sentence (- sentence_pos 1))
                      (get_pos sentence (- sentence_pos 1)))
        (lambda () (sample_word_id))
        (lambda () (get_word_id sentence (- sentence_pos 1))))))))
""")

  v.assume("get_pos","""
(mem (lambda (sentence sentence_pos)
  (branch (= sentence_pos 0)
    (lambda () 0)
    (lambda ()
      (branch (is_end (get_word_id sentence (- sentence_pos 1))
                      (get_pos sentence (- sentence_pos 1)))
        (lambda () 0)
        (lambda () (+ (get_pos sentence (- sentence_pos 1)) 1)))))))
""")

  v.assume("sample_symbol","""
(mem (lambda (sentence sentence_pos)
  (sample_letter_in_word (get_word_id sentence sentence_pos) (get_pos sentence sentence_pos))))
""")

#  v.assume("noise","(gamma 1 1)")
  v.assume("noise",".01")
  v.assume("noisy_true","(lambda (pred noise) (flip (if pred 1.0 noise)))")


  for i in range(len(brent)): #for each sentence
    for j in range(len(brent[i])): #for each letter
      v.predict("(sample_symbol %d %d)" %(i, j))
      v.observe("(noisy_true (atom_eq (sample_symbol %d %d) atom<%d>) noise)" %(i, j,d[str(brent[i][j])]), "true")

  v.infer(N)
  return reportPassage("TestGoldwater1")


def testMemHashFunction1(A,B):
  ripl = RIPL()
  ripl.assume("f","(mem (lambda (a b) (normal 0.0 1.0)))")
  for a in range(A):
    for b in range(B):
      ripl.observe("(f %d %d)" % (a,b),"0.5")
  return reportPassage("TestMemHashFunction(%d,%d)" % (A,B))


###########################
###### DSELSAM (madness) ##
###########################
def testDHSCRP1(N):
  ripl = RIPL()

  ripl.assume("dpmem","""
(lambda (alpha base_dist)
  ((lambda (augmented_proc crp)
     (lambda () (augmented_proc (crp))))
   (mem (lambda (table) (base_dist)))
   (make_crp alpha)))
""")

#  ripl.assume("alpha","(gamma 1.0 1.0)")
  ripl.assume("alpha","1.0")
  ripl.assume("base_dist","(lambda () (categorical 0.2 0.2 0.2 0.2 0.2))")
  ripl.assume("f","(dpmem alpha base_dist)")

  ripl.predict("(f)",label="pid")

  observeCategories(ripl,[2,2,5,1,0])

  predictions = collectSamples(ripl,"pid",N)
  ans = [(0,2.2), (1,2.2), (2,5.2), (3,1.2), (4,0.2)]
  return reportKnownDiscrete("TestDHSCRP1", ans, predictions)

def testDHSCRP2(N):
  ripl = RIPL()
  loadDPMem(ripl)

  ripl.assume("alpha","1.0")

  ripl.assume("base_dist","(lambda () (categorical 0.2 0.2 0.2 0.2 0.2))")
  ripl.assume("f","(u_dpmem alpha base_dist)")

  ripl.predict("(f)",label="pid")

  observeCategories(ripl,[2,2,5,1,0])

  predictions = collectSamples(ripl,"pid",N)
  ans = [(0,2.2), (1,2.2), (2,5.2), (3,1.2), (4,0.2)]
  return reportKnownDiscrete("TestDHSCRP2", ans, predictions)





def testPGibbsBlockingMHHMM1(N):
  ripl = RIPL()

  ripl.assume("x0","(scope_include 0 0 (normal 0.0 1.0))")
  ripl.assume("x1","(scope_include 0 1 (normal x0 1.0))")
  ripl.assume("x2","(scope_include 0 2 (normal x1 1.0))")
  ripl.assume("x3","(scope_include 0 3 (normal x2 1.0))")
  ripl.assume("x4","(scope_include 0 4 (normal x3 1.0))")

  ripl.assume("y0","(normal x0 1.0)")
  ripl.assume("y1","(normal x1 1.0)")
  ripl.assume("y2","(normal x2 1.0)")
  ripl.assume("y3","(normal x3 1.0)")
  ripl.assume("y4","(normal x4 1.0)")

  ripl.observe("y0",1.0)
  ripl.observe("y1",2.0)
  ripl.observe("y2",3.0)
  ripl.observe("y3",4.0)
  ripl.observe("y4",5.0)
  ripl.predict("x4")

  predictions = collectSamplesWith(ripl,16,N,{"kernel":"pgibbs","transitions":10,"scope":0,"block":"ordered"})
  reportKnownMeanVariance("TestPGibbsBlockingMHHMM1", 390/89.0, 55/89.0, predictions)
  cdf = stats.norm(loc=390/89.0, scale=math.sqrt(55/89.0)).cdf
  return reportKnownContinuous("TestPGibbsBlockingMHHMM1", cdf, predictions, "N(4.382, 0.786)")

##########

