# Copyright (c) 2013, 2014, 2015 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

from venture.test.stats import statisticalTest, reportKnownMean
from nose.tools import eq_, raises
from venture.test.config import get_ripl, collectSamples, collectStateSequence, skipWhenRejectionSampling, on_inf_prim, gen_on_inf_prim
from testconfig import config
from nose import SkipTest

def checkConstrainAVar1a(program):
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")
  ripl.observe("(if (tag 0 0 (flip)) x y)", 3.0)
  ripl.predict("x", label="pid")
  # Not collectSamples because we depend on the trace being in a
  # non-reset state at the end
  collectStateSequence(ripl,"pid",infer=program)
  eq_(ripl.report("pid"), 3)

def checkConstrainAVar1b(program):
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")
  ripl.predict("x", label="pid")
  ripl.observe("(if (tag 0 0 (flip)) x y)", 3.0)
  # Not collectSamples because we depend on the trace being in a
  # non-reset state at the end
  collectStateSequence(ripl,"pid",infer=program)
  eq_(ripl.report("pid"), 3)

def checkConstrainAVar2a(program):
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")
  ripl.assume("f","(mem (lambda () (tag 0 0 (flip))))")
  ripl.predict("(if (f) x y)", label="pid")
  ripl.observe("(if (f) x y)", 3.0)
  # Not collectSamples because we depend on the trace being in a
  # non-reset state at the end
  collectStateSequence(ripl,"pid",infer=program)
  eq_(ripl.report("pid"), 3)

def checkConstrainAVar2b(program):
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")
  ripl.assume("f","(mem (lambda () (tag 0 0 (flip))))")
  ripl.predict("(if (not (f)) x y)", label="pid")
  ripl.observe("(if (f) x y)", 3.0)
  # Not collectSamples because we depend on the trace being in a
  # non-reset state at the end
  collectStateSequence(ripl,"pid",infer=program)
  eq_(ripl.report("pid"), 3)

@on_inf_prim("mh")
def testConstrainAVar3a():
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")
  ripl.assume("f","(mem (lambda () (flip)))")
  ripl.predict("x", label="pid")
  ripl.observe("(if (f) x y)", 3.0)
  ripl.observe("(f)","true")
  ripl.infer("(mh default one 50)")
  eq_(ripl.report("pid"), 3)

# @raises(Exception)
@on_inf_prim("mh")
def testConstrainAVar3b():
  raise SkipTest("This program is illegal, since propagating from (f) reaches a request")
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")
  ripl.assume("f","(mem (lambda () (flip)))")
  ripl.observe("(if (f) x y)", 3.0)
  ripl.predict("x", label="pid")
  ripl.observe("(f)","true")
  ripl.infer("(mh default one 50)")
  eq_(ripl.report("pid"), 3)

def checkConstrainAVar4a(program):
  """We allow downstream processing with no requests and no randomness."""
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")
  ripl.assume("f","(mem (lambda () (tag 0 0 (flip))))")
  ripl.predict("(if (f) (* x 5) (* y 5))", label="pid")
  ripl.observe("(if (f) x y)", 3.0)
  # Not collectSamples because we depend on the trace being in a
  # non-reset state at the end
  collectStateSequence(ripl,"pid",infer=program)
  eq_(ripl.report("pid"), 15.0)

def checkConstrainAVar4b(program):
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")
  ripl.assume("f","(mem (lambda () (tag 0 0 (flip))))")
  ripl.predict("(if (not (f)) (* x 5) (* y 5))", label="pid")
  ripl.observe("(if (f) x y)", 3.0)
  # Not collectSamples because we depend on the trace being in a
  # non-reset state at the end
  collectStateSequence(ripl,"pid",infer=program)
  eq_(ripl.report("pid"), 15.0)

def checkConstrainAVar4c(program):
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")
  ripl.assume("f","(mem (lambda () (tag 0 0 (flip))))")
  ripl.predict("(* x 5)", label="pid")
  ripl.observe("(if (f) x y)", 3.0)
  # Not collectSamples because we depend on the trace being in a
  # non-reset state at the end
  collectStateSequence(ripl,"pid",infer=program)
  eq_(ripl.report("pid"), 15.0)

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
  ripl.assume("f","(mem (lambda () (tag 0 0 (flip))))")
  ripl.predict("(normal x 0.0001)")
  ripl.observe("(if (f) x y)", 3.0)
  collectSamples(ripl,"pid",infer=program)

@raises(Exception)
def checkConstrainAVar5b(program):
  """
    This program is illegal, because when proposing to f, we may end up constraining x,
    and x has a child in A (it is in the (new)brush itself).
  """
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")
  ripl.assume("f","(mem (lambda () (tag 0 0 (flip))))")
  ripl.predict("(if (f) (normal x 0.0001) (normal y 0.0001))")
  ripl.observe("(if (f) x y)", 3.0)
  collectSamples(ripl,"pid",infer=program)

@raises(Exception)
def checkConstrainAVar6a(program):
  """
    This program is illegal, because when proposing to f, we may end up constraining x,
    and x has a child that makes requests.
  """
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")
  ripl.assume("f","(mem (lambda () (tag 0 0 (flip))))")
  ripl.predict("(if (< (normal x 1.0) 3) x y)")
  ripl.observe("(if (f) x y)", 3.0)
  collectSamples(ripl,"pid",infer=program)

@raises(Exception)
def checkConstrainAVar6b(program):
  """
    This program is illegal, because when proposing to f, we may end up constraining x,
    and x has a child that makes requests.
  """
  ripl = get_ripl()
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("y","(normal 0.0 1.0)")
  ripl.assume("f","(mem (lambda () (tag 0 0 (flip))))")
  ripl.observe("(if (f) x y)", 3.0)
  ripl.predict("(if (< (normal x 1.0) 3) x y)")
  collectSamples(ripl,"pid",infer=program)

@gen_on_inf_prim("all") # TODO Segregate generated tests by inference method
def testConstrainWithAPredict1():
  if config["get_ripl"] != "lite": raise SkipTest("assert(false) crashes NoseTests")
  for p in ["(mh default one 50)",
            "(rejection default all 50)",
            "(func_pgibbs default ordered 3 50 false)",
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

@skipWhenRejectionSampling("Rejection sampling doesn't work when resimulations of unknown code are observed")
@statisticalTest
def testConstrainWithAPredict2():
  """This test will fail at first, since we previously considered a program like this to be illegal
     and thus did not handle it correctly (we let the predict go stale). So we do not continually
     bewilder our users, I suggest that we handle this case WHEN WE CAN, which means we propagate
     from a constrain as long as we don't hit an absorbing node or a DRG node with a kernel."""
  ripl = get_ripl()
  ripl.assume("f","(if (flip) (lambda () (normal 0.0 1.0)) (mem (lambda () (normal 0.0 1.0))))")
  ripl.observe("(f)","1.0")
  ripl.predict("(* (f) 100)",label="pid")
  predictions = collectSamples(ripl,"pid")
  return reportKnownMean(50, predictions) # will divide by 0 if there is no sample variance

@on_inf_prim("mh")
def testConstrainInAScope1():
  """At some point, constrain did not remove choices from scopes besides the default scope"""
  ripl = get_ripl()

  ripl.assume("x","(tag 0 0 (normal 0 1))")
  ripl.observe("x","1")
  ripl.predict("(normal x 1)")

  ripl.infer("(mh 0 0 10)")

@on_inf_prim("mh")
def testConstrainInAScope2brush():
  """Particles need to override some of the relevant methods as well"""
  ripl = get_ripl()

  ripl.assume("x","(tag 0 0 (if (flip) (normal 0 1) (normal 0 1)))")
  ripl.observe("x","1")
  ripl.predict("(+ x 1)")

  ripl.infer("(mh 0 0 20)")

@on_inf_prim("pgibbs")
def testConstrainInAScope2particles():
  """Particles need to override some of the relevant methods as well"""
  ripl = get_ripl()

  ripl.assume("x","(tag 0 0 (if (flip) (normal 0 1) (normal 0 1)))")
  ripl.observe("x","1")
  ripl.predict("(+ x 1)")

  ripl.infer("(pgibbs 0 0 5 5)")

@gen_on_inf_prim("mh")
def testMHConstrains():
  for t in [checkConstrainAVar1a, checkConstrainAVar1b,
            checkConstrainAVar2a, checkConstrainAVar2b,
            checkConstrainAVar4a, checkConstrainAVar4b, checkConstrainAVar4c,
            checkConstrainAVar5a, checkConstrainAVar5b,
            checkConstrainAVar6a, checkConstrainAVar6b]:
    yield t, "(mh 0 0 50)"

@gen_on_inf_prim("func_pgibbs")
def testFuncPGibbsConstrains():
  for t in [checkConstrainAVar1a, checkConstrainAVar1b,
            checkConstrainAVar2a, checkConstrainAVar2b,
            checkConstrainAVar4a, checkConstrainAVar4b, checkConstrainAVar4c]:
    yield t, "(func_pgibbs 0 0 3 50)"
  for t in [checkConstrainAVar5a, checkConstrainAVar5b,
            checkConstrainAVar6a, checkConstrainAVar6b]:
    yield t, "(func_pgibbs 0 0 3 50 false)"

@gen_on_inf_prim("pgibbs")
def testPGibbsConstrains():
  for t in [checkConstrainAVar1a, checkConstrainAVar1b,
            checkConstrainAVar2a, checkConstrainAVar2b,
            checkConstrainAVar4a, checkConstrainAVar4b, checkConstrainAVar4c]:
    yield t, "(pgibbs 0 0 3 50)"
  for t in [checkConstrainAVar5a, checkConstrainAVar5b,
            checkConstrainAVar6a, checkConstrainAVar6b]:
    yield t, "(pgibbs 0 0 3 50 false)"

@gen_on_inf_prim("gibbs")
def testGibbsConstrains():
  for t in [checkConstrainAVar1a, checkConstrainAVar1b,
            checkConstrainAVar2a, checkConstrainAVar2b,
            checkConstrainAVar4a, checkConstrainAVar4b, checkConstrainAVar4c]:
    yield t, "(gibbs 0 0 50)"
  for t in [checkConstrainAVar5a, checkConstrainAVar5b,
            checkConstrainAVar6a, checkConstrainAVar6b]:
    yield t, "(gibbs 0 0 50 false)"

@gen_on_inf_prim("rejection")
def testRejectionConstrains():
  # Rejection sampling doesn't work when resimulations of unknown code are observed
  for t in [checkConstrainAVar5a, checkConstrainAVar5b,
            checkConstrainAVar6a, checkConstrainAVar6b]:
    yield t, "(rejection 0 0 50)"
