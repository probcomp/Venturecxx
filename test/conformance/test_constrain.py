from venture.test.stats import statisticalTest, reportKnownMean
from nose.tools import eq_, raises
from venture.test.config import get_ripl, collectSamples, defaultKernel, collectStateSequence
from testconfig import config
from nose import SkipTest

def testConstrainAVar1a():
  if defaultKernel() is not "mh":
    raise SkipTest("Ignores the inference program, so do not repeat")
  for p in ["(mh 0 0 50)",
            # Rejection sampling doesn't work when resimulations of unknown code are observed
            "(func-pgibbs 0 0 3 50)",
            "(pgibbs 0 0 3 50)",
            "(gibbs 0 0 50)",
            ]:
    yield checkConstrainAVar1a, p

def checkConstrainAVar1a(program):
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")
  ripl.observe("(if (scope_include 0 0 (flip)) x y)", 3.0)
  ripl.predict("x", label="pid")
  # Not collectSamples because we depend on the trace being in a
  # non-reset state at the end
  collectStateSequence(ripl,"pid",infer=program)
  eq_(ripl.report("pid"), 3)

def testConstrainAVar1b():
  if defaultKernel() is not "mh":
    raise SkipTest("Ignores the inference program, so do not repeat")
  for p in ["(mh 0 0 50)",
            # Rejection sampling doesn't work when resimulations of unknown code are observed
            "(func-pgibbs 0 0 3 50)",
            "(pgibbs 0 0 3 50)",
            "(gibbs 0 0 50)",
            ]:
    yield checkConstrainAVar1b, p

def checkConstrainAVar1b(program):
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")
  ripl.predict("x", label="pid")
  ripl.observe("(if (scope_include 0 0 (flip)) x y)", 3.0)
  # Not collectSamples because we depend on the trace being in a
  # non-reset state at the end
  collectStateSequence(ripl,"pid",infer=program)
  eq_(ripl.report("pid"), 3)

def testConstrainAVar2a():
  if defaultKernel() is not "mh":
    raise SkipTest("Ignores the inference program, so do not repeat")
  for p in ["(mh 0 0 50)",
            # Rejection sampling doesn't work when resimulations of unknown code are observed
            "(func-pgibbs 0 0 3 50)",
            "(pgibbs 0 0 3 50)",
            "(gibbs 0 0 50)",
            ]:
    yield checkConstrainAVar2a, p

def checkConstrainAVar2a(program):
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")
  ripl.assume("f","(mem (lambda () (scope_include 0 0 (flip))))")
  ripl.predict("(if (f) x y)", label="pid")
  ripl.observe("(if (f) x y)", 3.0)
  # Not collectSamples because we depend on the trace being in a
  # non-reset state at the end
  collectStateSequence(ripl,"pid",infer=program)
  eq_(ripl.report("pid"), 3)

def testConstrainAVar2b():
  if defaultKernel() is not "mh":
    raise SkipTest("Ignores the inference program, so do not repeat")
  for p in ["(mh 0 0 50)",
            # Rejection sampling doesn't work when resimulations of unknown code are observed
            "(func-pgibbs 0 0 3 50)",
            "(pgibbs 0 0 3 50)",
            "(gibbs 0 0 50)",
            ]:
    yield checkConstrainAVar2b, p

def checkConstrainAVar2b(program):
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")
  ripl.assume("f","(mem (lambda () (scope_include 0 0 (flip))))")
  ripl.predict("(if (not (f)) x y)", label="pid")
  ripl.observe("(if (f) x y)", 3.0)
  # Not collectSamples because we depend on the trace being in a
  # non-reset state at the end
  collectStateSequence(ripl,"pid",infer=program)
  eq_(ripl.report("pid"), 3)

def checkConstrainAVar3a():
  if defaultKernel() is not "mh":
    raise SkipTest("Ignores the inference program, so do not repeat")
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")
  ripl.assume("f","(mem (lambda () (flip)))")
  ripl.predict("x", label="pid")
  ripl.observe("(if (f) x y)", 3.0)
  ripl.observe("(f)","true")
  ripl.infer("(mh default one 50)")
  #  ripl.sivm.core_sivm.engine.infer({"kernel":"mh","transitions":50})
  eq_(ripl.report("pid"), 3)

# @raises(Exception)
def testConstrainAVar3b():
  raise SkipTest("This program is illegal, since propagating from (f) reaches a request")
  if defaultKernel() is not "mh":
    raise SkipTest("Ignores the inference program, so do not repeat")
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")
  ripl.assume("f","(mem (lambda () (flip)))")
  ripl.observe("(if (f) x y)", 3.0)
  ripl.predict("x", label="pid")
  ripl.observe("(f)","true")
  ripl.infer("(mh default one 50)")
  # ripl.sivm.core_sivm.engine.infer({"kernel":"mh","transitions":50})
  eq_(ripl.report("pid"), 3)

def testConstrainAVar4a():
  if defaultKernel() is not "mh":
    raise SkipTest("Ignores the inference program, so do not repeat")
  for p in ["(mh 0 0 50)",
            # Rejection sampling doesn't work when resimulations of unknown code are observed
            "(func-pgibbs 0 0 3 50)",
            "(pgibbs 0 0 3 50)",
            "(gibbs 0 0 50)",
            ]:
    yield checkConstrainAVar4a, p

def checkConstrainAVar4a(program):
  """We allow downstream processing with no requests and no randomness."""
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")
  ripl.assume("f","(mem (lambda () (scope_include 0 0 (flip))))")
  ripl.predict("(if (f) (* x 5) (* y 5))", label="pid")
  ripl.observe("(if (f) x y)", 3.0)
  # Not collectSamples because we depend on the trace being in a
  # non-reset state at the end
  collectStateSequence(ripl,"pid",infer=program)
  eq_(ripl.report("pid"), 15.0)

def testConstrainAVar4b():
  if defaultKernel() is not "mh":
    raise SkipTest("Ignores the inference program, so do not repeat")
  for p in ["(mh 0 0 50)",
            # Rejection sampling doesn't work when resimulations of unknown code are observed
            "(func-pgibbs 0 0 3 50)",
            "(pgibbs 0 0 3 50)",
            "(gibbs 0 0 50)",
            ]:
    yield checkConstrainAVar4b, p

def checkConstrainAVar4b(program):
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")
  ripl.assume("f","(mem (lambda () (scope_include 0 0 (flip))))")
  ripl.predict("(if (not (f)) (* x 5) (* y 5))", label="pid")
  ripl.observe("(if (f) x y)", 3.0)
  # Not collectSamples because we depend on the trace being in a
  # non-reset state at the end
  collectStateSequence(ripl,"pid",infer=program)
  eq_(ripl.report("pid"), 15.0)

def testConstrainAVar4c():
  if defaultKernel() is not "mh":
    raise SkipTest("Ignores the inference program, so do not repeat")
  for p in ["(mh 0 0 50)",
            # Rejection sampling doesn't work when resimulations of unknown code are observed
            "(func-pgibbs 0 0 3 50)",
            "(pgibbs 0 0 3 50)",
            "(gibbs 0 0 50)",
            ]:
    yield checkConstrainAVar4c, p

def checkConstrainAVar4c(program):
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")
  ripl.assume("f","(mem (lambda () (scope_include 0 0 (flip))))")
  ripl.predict("(* x 5)", label="pid")
  ripl.observe("(if (f) x y)", 3.0)
  # Not collectSamples because we depend on the trace being in a
  # non-reset state at the end
  collectStateSequence(ripl,"pid",infer=program)
  eq_(ripl.report("pid"), 15.0)

def testConstrainAVar5a():
  if defaultKernel() is not "mh":
    raise SkipTest("Ignores the inference program, so do not repeat")
  for p in ["(mh 0 0 50)",
            "(rejection 0 0 50)",
            "(func-pgibbs 0 0 3 50 false)",
            "(pgibbs 0 0 3 50 false)",
            "(gibbs 0 0 50 false)",
            ]:
    yield checkConstrainAVar5a, p

@raises(Exception)
def checkConstrainAVar5a(program):
  """
    This program is illegal, because when proposing to f, we may end up constraining x,
    which needs to be propagated but the propagation reaches a random choice. This could
    in principle be allowed because there is no exchangeable couping, but for now we have
    decided to forbid all non-identity downstream edges.
  """
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")
  ripl.assume("f","(mem (lambda () (scope_include 0 0 (flip))))")
  ripl.predict("(normal x 0.0001)")
  ripl.observe("(if (f) x y)", 3.0)
  collectSamples(ripl,"pid",infer=program)

def testConstrainAVar5b():
  if defaultKernel() is not "mh":
    raise SkipTest("Ignores the inference program, so do not repeat")
  for p in ["(mh 0 0 50)",
            "(rejection 0 0 50)",
            "(func-pgibbs 0 0 3 50 false)",
            "(pgibbs 0 0 3 50 false)",
            "(gibbs 0 0 50 false)",
            ]:
    yield checkConstrainAVar5b, p

@raises(Exception)
def checkConstrainAVar5b(program):
  """
    This program is illegal, because when proposing to f, we may end up constraining x,
    and x has a child in A (it is in the (new)brush itself).
  """
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")
  ripl.assume("f","(mem (lambda () (scope_include 0 0 (flip))))")
  ripl.predict("(if (f) (normal x 0.0001) (normal y 0.0001))")
  ripl.observe("(if (f) x y)", 3.0)
  collectSamples(ripl,"pid",infer=program)

def testConstrainAVar6a():
  if defaultKernel() is not "mh":
    raise SkipTest("Ignores the inference program, so do not repeat")
  for p in ["(mh 0 0 50)",
            "(rejection 0 0 50)",
            "(func-pgibbs 0 0 3 50 false)",
            "(pgibbs 0 0 3 50 false)",
            "(gibbs 0 0 50 false)",
            ]:
    yield checkConstrainAVar6a, p

@raises(Exception)
def checkConstrainAVar6a(program):
  """
    This program is illegal, because when proposing to f, we may end up constraining x,
    and x has a child that makes requests.
  """
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")
  ripl.assume("f","(mem (lambda () (scope_include 0 0 (flip))))")
  ripl.predict("(if (< (normal x 1.0) 3) x y)")
  ripl.observe("(if (f) x y)", 3.0)
  collectSamples(ripl,"pid",infer=program)

def testConstrainAVar6b():
  if defaultKernel() is not "mh":
    raise SkipTest("Ignores the inference program, so do not repeat")
  for p in ["(mh 0 0 50)",
            "(rejection 0 0 50)",
            "(func-pgibbs 0 0 3 50 false)",
            "(pgibbs 0 0 3 50 false)",
            "(gibbs 0 0 50 false)",
            ]:
    yield checkConstrainAVar6b, p

@raises(Exception)
def checkConstrainAVar6b(program):
  """
    This program is illegal, because when proposing to f, we may end up constraining x,
    and x has a child that makes requests.
  """
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")
  ripl.assume("f","(mem (lambda () (scope_include 0 0 (flip))))")
  ripl.observe("(if (f) x y)", 3.0)
  ripl.predict("(if (< (normal x 1.0) 3) x y)")
  collectSamples(ripl,"pid",infer=program)

def testConstrainWithAPredict1():
  if config["get_ripl"] != "lite": raise SkipTest("assert(false) crashes NoseTests")
  if defaultKernel() is not "mh":
    raise SkipTest("Ignores the inference program, so do not repeat")
  for p in ["(mh default one 50)",
            "(rejection default all 50)",
            "(func-pgibbs default ordered 3 50 false)",
            "(pgibbs default ordered 3 50 false)",
            "(meanfield default one 50)",
            ]:
    yield checkConstrainWithAPredict1, p

@raises(Exception)
def checkConstrainWithAPredict1(program):
  """
  We may constrain the (flip) in f, and this has a child that makes requests. Therefore this
  should (currently) throw an exception.
  """
  ripl = get_ripl()
  ripl.assume("f","(mem (lambda () (flip)))")
  ripl.assume("op1","(if (flip) flip (lambda () (f)))")
  ripl.assume("op2","(if (op1) op1 (lambda () (op1)))")
  ripl.assume("op3","(if (op2) op2 (lambda () (op2)))")
  ripl.assume("op4","(if (op3) op2 op1)")
  ripl.predict("(op4)")
  ripl.observe("(op4)",True)
  collectSamples(ripl,"pid",infer=program)

@statisticalTest
def testConstrainWithAPredict2():
  """This test will fail at first, since we previously considered a program like this to be illegal
     and thus did not handle it correctly (we let the predict go stale). So we do not continually
     bewilder our users, I suggest that we handle this case WHEN WE CAN, which means we propagate
     from a constrain as long as we don't hit an absorbing node or a DRG node with a kernel."""
  if defaultKernel() == "rejection":
    raise SkipTest("Rejection sampling doesn't work when resimulations of unknown code are observed")
  ripl = get_ripl()
  ripl.assume("f","(if (flip) (lambda () (normal 0.0 1.0)) (mem (lambda () (normal 0.0 1.0))))")
  ripl.observe("(f)","1.0")
  ripl.predict("(* (f) 100)",label="pid")
  predictions = collectSamples(ripl,"pid")
  return reportKnownMean(50, predictions) # will divide by 0 if there is no sample variance

def testConstrainInAScope1():
  """At some point, constrain did not remove choices from scopes besides the default scope"""
  ripl = get_ripl()

  ripl.assume("x","(scope_include 0 0 (normal 0 1))")
  ripl.observe("x","1")
  ripl.predict("(normal x 1)")

  ripl.infer("(mh 0 0 10)")

def testConstrainInAScope2brush():
  """Particles need to override some of the relevant methods as well"""
  ripl = get_ripl()

  ripl.assume("x","(scope_include 0 0 (if (flip) (normal 0 1) (normal 0 1)))")
  ripl.observe("x","1")
  ripl.predict("(+ x 1)")

  ripl.infer("(mh 0 0 20)")

def testConstrainInAScope2particles():
  """Particles need to override some of the relevant methods as well"""
  ripl = get_ripl()

  ripl.assume("x","(scope_include 0 0 (if (flip) (normal 0 1) (normal 0 1)))")
  ripl.observe("x","1")
  ripl.predict("(+ x 1)")

  ripl.infer("(pgibbs 0 0 5 5)")
  



