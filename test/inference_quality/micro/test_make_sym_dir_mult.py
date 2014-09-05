from nose import SkipTest
from venture.test.stats import statisticalTest, reportKnownDiscrete
from venture.test.config import get_ripl, collectSamples, skipWhenRejectionSampling, rejectionSampling, skipWhenSubSampling

# TODO this whole file will need to be parameterized.
# Most of these will become "check" functions instead of "test"
# functions, and then we will have a few test-generators.

# TODO this folder needs many more interesting test cases!

############## (1) Test SymDirMult AAA

#
def testMakeSymDirMult1():
  for maker in ["make_sym_dir_mult","make_uc_sym_dir_mult"]:
    yield checkMakeSymDirMult1, maker

@statisticalTest
def checkMakeSymDirMult1(maker):
  """Extremely simple program, with an AAA procedure when uncollapsed"""
  ripl = get_ripl()
  ripl.assume("f", "(%s 1.0 2)" % maker)
  ripl.predict("(f)",label="pid")
  predictions = collectSamples(ripl,"pid")
  ans = [(0,.5), (1,.5)]
  return reportKnownDiscrete(ans, predictions)

def testMakeSymDirMultAAA():
  for maker in ["make_sym_dir_mult","make_uc_sym_dir_mult"]:
    yield checkMakeSymDirMultAAA,maker

@statisticalTest
def checkMakeSymDirMultAAA(maker):
  """Simplest program with collapsed AAA"""
  ripl = get_ripl()

  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "(%s a 4)" % maker)
  ripl.predict("(f)",label="pid")
  return checkDirichletMultinomialAAA(ripl, "pid")

def testMakeSymDirMultFlip():
  """AAA where the SP flips between collapsed and uncollapsed."""
  for maker_1 in ["make_sym_dir_mult","make_uc_sym_dir_mult"]:
    for maker_2 in ["make_sym_dir_mult","make_uc_sym_dir_mult"]:
      yield checkMakeSymDirMultFlip,maker_1,maker_2
  
@skipWhenRejectionSampling("Rejection sampling doesn't work when resimulations of unknown code are observed")
@skipWhenSubSampling("Leads to a scaffold structure that the current implementation of subsampling can't handle")
@statisticalTest
def checkMakeSymDirMultFlip(maker_1,maker_2):
  ripl = get_ripl()

  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "((if (lt a 10) %s %s) a 4)" % (maker_1,maker_2))
  ripl.predict("(f)",label="pid")
  return checkDirichletMultinomialAAA(ripl, "pid")

def testMakeSymDirMultBrushObserves():
  """AAA where the SP flips between collapsed and uncollapsed, and
     there are observations in the brush."""
  for maker_1 in ["make_sym_dir_mult","make_uc_sym_dir_mult"]:
    for maker_2 in ["make_sym_dir_mult","make_uc_sym_dir_mult"]:
      yield checkMakeSymDirMultBrushObserves,maker_1,maker_2

@skipWhenRejectionSampling("Rejection sampling doesn't work when resimulations of unknown code are observed")
@skipWhenSubSampling("Leads to a scaffold structure that the current implementation of subsampling can't handle")
@statisticalTest
def checkMakeSymDirMultBrushObserves(maker_1,maker_2):
  ripl = get_ripl()

  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "((if (lt a 10) %s %s) a 2)" % (maker_1,maker_2))
  ripl.predict("(f)",label="pid")

  return checkDirichletMultinomialBrush(ripl,"pid")

@skipWhenRejectionSampling("Rejection sampling doesn't work when resimulations of unknown code are observed")
@skipWhenSubSampling("Leads to a scaffold structure that the current implementation of subsampling can't handle")
@statisticalTest
def testMakeSymDirMultNative():
  """AAA where the SP flips between collapsed, uncollapsed, and native"""
  ripl = get_ripl()

  ripl.assume("a", "(normal 10.0 1.0)")
# Might be collapsed, uncollapsed, or uncollapsed in Venture
  ripl.assume("f","""
((if (lt a 9.5) 
     make_sym_dir_mult 
     (if (lt a 10.5)
         make_uc_sym_dir_mult
         (lambda (alpha k) 
           ((lambda (theta) (lambda () (categorical theta)))
            (symmetric_dirichlet alpha k)))))
 a 4)
""")
  ripl.predict("(f)",label="pid")
  return checkDirichletMultinomialAAA(ripl, "pid")

def testMakeSymDirMultAppControlsFlip():
  for maker_1 in ["make_sym_dir_mult","make_uc_sym_dir_mult"]:
    for maker_2 in ["make_sym_dir_mult","make_uc_sym_dir_mult"]:
      yield checkMakeSymDirMultAppControlsFlip,maker_1,maker_2

@statisticalTest
def checkMakeSymDirMultAppControlsFlip(maker_1,maker_2):
  """Two AAA SPs with same parameters, where their applications control which are applied"""
  ripl = get_ripl()

  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "(%s a 4)" % maker_1)
  ripl.assume("g", "(%s a 4)" % maker_2)
  ripl.predict("(f)",label="pid")
  ripl.predict("(g)")
  for _ in range(5): ripl.observe("(g)","atom<1>")
  ripl.predict("(if (eq (f) atom<1>) (g) (g))")
  ripl.predict("(if (eq (g) atom<1>) (f) (f))")
  return checkDirichletMultinomialAAA(ripl, "pid", infer="mixes_slowly")

def testMakeDirMult1():
  for maker in ["make_dir_mult","make_uc_dir_mult"]:
    yield checkMakeDirMult1,maker

@statisticalTest
def checkMakeDirMult1(maker):
  if rejectionSampling() and maker == "make_dir_mult":
    raise SkipTest("Is the log density of counts bounded for collapsed beta bernoulli?  Issue: https://app.asana.com/0/9277419963067/10623454782852")
  ripl = get_ripl()

  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "(%s (array a a a a))" % maker)
  ripl.predict("(f)", label="pid")
  return checkDirichletMultinomialAAA(ripl, "pid")

def testMakeSymDirMultWeakPrior():
  """This used to fail because nothing ever got unincorporated. Should work now"""
  for maker in ["make_sym_dir_mult","make_uc_sym_dir_mult"]:
    yield checkMakeSymDirMultWeakPrior,maker

@statisticalTest
def checkMakeSymDirMultWeakPrior(maker):
  ripl = get_ripl()

  ripl.assume("a", "1.0")
  ripl.assume("f", "(%s a 2)" % maker)
  ripl.predict("(f)",label="pid")

  return checkDirichletMultinomialWeakPrior(ripl,"pid")


#### Staleness

@statisticalTest
def testStaleAAA_MSP():
  ripl = get_ripl()

  ripl.assume("a", "1.0")
  ripl.assume("f", "(make_uc_sym_dir_mult a 2)")
  ripl.assume("g", "(mem f)")
  ripl.assume("h", "g")
  ripl.predict("(h)",label="pid")

  return checkDirichletMultinomialWeakPrior(ripl,"pid")  

@statisticalTest
def testStaleAAA_CSP():
  ripl = get_ripl()

  ripl.assume("a", "1.0")
  ripl.assume("f", "(make_uc_sym_dir_mult a 2)")
  ripl.assume("g", "(lambda () f)")
  ripl.assume("h", "(g)")
  ripl.predict("(h)",label="pid")

  return checkDirichletMultinomialWeakPrior(ripl,"pid")  
 
@statisticalTest
def testStaleAAA_Madness():
  ripl = get_ripl()

  ripl.assume("make_ref","(lambda (x) (lambda () x))")
  ripl.assume("deref","(lambda (x) (x))")

  ripl.assume("a", "1.0")
  ripl.assume("f", "(make_uc_sym_dir_mult a 2)")
  ripl.assume("f2_maker", "(lambda () f)")
  ripl.assume("f2", "(f2_maker)")
  ripl.assume("xs", "(array (make_ref f) (make_ref f2))")
  ripl.assume("f3","(deref (lookup xs 1))")
  ripl.assume("ys","(dict (array (quote aaa) (quote bbb)) (array (make_ref f3) (make_ref f3)))")
  ripl.assume("g","(deref (if (flip) (lookup ys (quote aaa)) (lookup ys (quote bbb))))")
  ripl.predict("(g)",label="pid")

  return checkDirichletMultinomialWeakPrior(ripl,"pid") 
 

#### Helpers

def checkDirichletMultinomialAAA(ripl, label, infer=None):
  for i in range(1,4):
    for _ in range(20):
      ripl.observe("(f)", "atom<%d>" % i)

  predictions = collectSamples(ripl,label,infer=infer)
  ans = [(0,.1), (1,.3), (2,.3), (3,.3)]
  return reportKnownDiscrete(ans, predictions)

def checkDirichletMultinomialBrush(ripl,label):
  for _ in range(10): ripl.observe("(f)","atom<1>")
  for _ in range(10): ripl.observe("""
(if (lt a 10.0)
  (f)
  (f))""","atom<1>")

  predictions = collectSamples(ripl,label)
  ans = [(0,.25), (1,.75)]
  return reportKnownDiscrete(ans, predictions)

def checkDirichletMultinomialWeakPrior(ripl,label):
  for _ in range(8):
    ripl.observe("(f)", "atom<1>")

  predictions = collectSamples(ripl,label,infer="mixes_slowly")
  ans = [(1,.9), (0,.1)]
  return reportKnownDiscrete(ans, predictions)

