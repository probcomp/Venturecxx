from venture.test.stats import *
from testconfig import config

# TODO this whole file will need to be parameterized.
# Most of these will become "check" functions instead of "test"
# functions, and then we will have a few test-generators.

# TODO this folder needs many more interesting test cases!

############## (1) Test SymDirMult AAA

# Test 1:1
def testMakeSymDirMult1():
  for maker in ["make_sym_dir_mult","make_uc_sym_dir_mult"]:
    yield checkMakeSymDirMult1,maker

def checkMakeSymDirMult1(maker):
  """Extremely simple program, with an AAA procedure when uncollapsed"""
  ripl = config["get_ripl"]()
  ripl.assume("f", "(%s 1.0 2)" % maker)
  ripl.predict("(f)",label="pid")
  predictions = collectSamples(ripl,"pid")
  ans = [(0,.5), (1,.5)]
  return reportKnownDiscrete("CheckMakeSymDirMult1(%s)" % maker, ans, predictions)

# Test 1:2
def testMakeSymDirMult2():
  for maker in ["make_sym_dir_mult","make_uc_sym_dir_mult"]:
    yield checkMakeSymDirMult2,maker

def checkMakeSymDirMult2(maker):
  """Simplest program with collapsed AAA"""
  ripl = config["get_ripl"]()

  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "(%s a 4)" % maker)
  ripl.predict("(f)",label="pid")
  return checkDirichletMultinomial1(maker, ripl, "pid")


# Test 1:3
def testMakeSymDirMult3():
  """AAA where the SP flips between collapsed and uncollapsed."""
  ripl = config["get_ripl"]()

  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "((if (lt a 10) make_sym_dir_mult make_uc_sym_dir_mult) a 4)")
  ripl.predict("(f)",label="pid")
  return checkDirichletMultinomial1("alternating collapsed/uncollapsed", ripl, "pid")

# Test 1:4
def testMakeSymDirMult4():
  """AAA where the SP flips between collapsed, uncollapsed, and native"""
  ripl = config["get_ripl"]()

  ripl.assume("a", "(normal 10.0 1.0)")
# Might be collapsed, uncollapsed, or uncollapsed in Venture
  ripl.assume("f","""
((if (lt a 10) 
     make_sym_dir_mult 
     (if (lt a 10.5)
         make_uc_sym_dir_mult
         (lambda (alpha k) 
           ((lambda (theta) (lambda () (categorical theta)))
            (symmetric_dirichlet alpha k)))))
 a 4)
""")
  ripl.predict("(f)",label="pid")
  return checkDirichletMultinomial1("alternating collapsed/uncollapsed-sp/uncollapsed-venture", ripl, "pid")


# Test 1:5
def testMakeSymDirMult5():
  for maker_1 in ["make_sym_dir_mult","make_uc_sym_dir_mult"]:
    for maker_2 in ["make_sym_dir_mult","make_uc_sym_dir_mult"]:
      yield checkMakeSymDirMult5,maker_1,maker_2

def checkMakeSymDirMult5(maker_1,maker_2):
  """Two AAA SPs with same parameters"""
  ripl = config["get_ripl"]()

  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "(%s a 4)" % maker_1)
  ripl.assume("g", "(%s a 4)" % maker_2)
  ripl.predict("(f)",label="pid")
  ripl.predict("(g)")
  for _ in range(5): ripl.observe("(g)","true")
  ripl.predict("(if (f) (g) (g))")
  ripl.predict("(if (g) (f) (f))")
  return checkDirichletMultinomial1(maker_1 + "&" + maker_2, ripl, "pid")


############# (2) Test Misc AAA

def testMakeSymDirMult1():
  for maker in ["make_dir_mult","make_uc_dir_mult"]:
    yield checkMakeDirMult1,maker

def checkMakeDirMult1(maker):
  ripl = config["get_ripl"]()

  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "(%s (simplex a a a a))" % maker)
  ripl.predict("(f)")
  return checkDirichletMultinomial1(maker, ripl, 3)

def testMakeBetaBernoulli1():
  for maker in ["make_beta_bernoulli","make_uc_beta_bernoulli"]:
    yield checkMakeBetaBernoulli1,maker

def checkMakeBetaBernoulli1(maker):
  ripl = config["get_ripl"]()

  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "(%s a a)" % maker)
  ripl.predict("(f)")

  for _ in range(20): ripl.observe("(f)", "true")

  predictions = collectSamples(ripl,3)
  ans = [(False,.25), (True,.75)]
  return reportKnownDiscrete("TestMakeBetaBernoulli1 (%s)" % maker, ans, predictions)

def testMakeBetaBernoulli2():
  for maker in ["make_beta_bernoulli","make_uc_beta_bernoulli"]:
    yield checkMakeBetaBernoulli2,maker

# These three represent mechanisable ways of fuzzing a program for
# testing language feature interactions (in this case AAA with
# constraint forwarding and brush).
def checkMakeBetaBernoulli2(maker):
  ripl = config["get_ripl"]()

  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "((lambda () (%s ((lambda () a)) ((lambda () a)))))" % maker)
  ripl.predict("(f)")

  for _ in range(20): ripl.observe("((lambda () (f)))", "true")

  predictions = collectSamples(ripl,3)
  ans = [(False,.25), (True,.75)]
  return reportKnownDiscrete("TestMakeBetaBernoulli2 (%s)" % maker, ans, predictions)

def testMakeBetaBernoulli3():
  for maker in ["make_beta_bernoulli","make_uc_beta_bernoulli"]:
    yield checkMakeBetaBernoulli3,maker

def checkMakeBetaBernoulli3(maker):
  ripl = config["get_ripl"]()

  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "(%s a a)" % maker)
  ripl.predict("(f)")

  for _ in range(10): ripl.observe("(f)", "true")
  for _ in range(10): ripl.observe("""
(if (lt a 10.0)
  (f)
  (f))""", "true")

  predictions = collectSamples(ripl,3)
  ans = [(False,.25), (True,.75)]
  return reportKnownDiscrete("TestMakeBetaBernoulli3 (%s)" % maker, ans, predictions)

def testMakeBetaBernoulli4():
  for maker in ["make_beta_bernoulli","make_uc_beta_bernoulli"]:
    yield checkMakeBetaBernoulli4,maker

def checkMakeBetaBernoulli4(maker):
  ripl = config["get_ripl"]()

  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", """
(if (lt a 10.0)
  ({0} a a)
  ({0} a a))""".format(maker))
  ripl.predict("(f)")

  for _ in range(20): ripl.observe("(f)", "true")

  predictions = collectSamples(ripl,3)
  ans = [(False,.25), (True,.75)]
  return reportKnownDiscrete("TestMakeBetaBernoulli4 (%s)" % maker, ans, predictions)


##### (3) Staleness

# TODO write better ones, and include arrays.
# This section should not hope to find staleness, since all backends should
# assert that a makerNode has been regenerated before applying it.
# Therefore this section should try to trigger that assertion.

def testStaleAAA1():
  ripl = config["get_ripl"]()

  ripl.assume("a", "1.0")
  ripl.assume("f", "(make_uc_sym_dir_mult a 2)")
  ripl.assume("g", "(mem f)")
  ripl.assume("h", "g")
  ripl.predict("(h)")

  for _ in range(9):
    ripl.observe("(f)", "atom<1>")

  predictions = collectSamples(ripl,5)
  ans = [(1,.9), (0,.1)]
  return reportKnownDiscrete("TestStaleAAA1", ans, predictions)

def testStaleAAA2():
  ripl = config["get_ripl"]()

  ripl.assume("a", "1.0")
  ripl.assume("f", "(make_uc_sym_dir_mult a 2)")
  ripl.assume("g", "(lambda () f)")
  ripl.assume("h", "(g)")
  ripl.predict("(h)")

  for _ in range(9):
    ripl.observe("(f)", "atom<1>")

  predictions = collectSamples(ripl,5)
  ans = [(1,.9), (0,.1)]
  return reportKnownDiscrete("TestStaleAAA2", ans, predictions)

#### Helpers

def checkDirichletMultinomial1(maker, ripl, label):
  for i in range(1,4):
    for _ in range(20):
      ripl.observe("(f)", "atom<%d>" % i)

  predictions = collectSamples(ripl,label)
  ans = [(0,.1), (1,.3), (2,.3), (3,.3)]
  return reportKnownDiscrete("CheckDirichletMultinomial(%s)" % maker, ans, predictions)
