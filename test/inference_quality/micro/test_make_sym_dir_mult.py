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

from nose import SkipTest
from nose.tools import eq_

from venture.test.config import broken_in
from venture.test.config import collectSamples
from venture.test.config import default_num_data
from venture.test.config import gen_broken_in
from venture.test.config import gen_on_inf_prim
from venture.test.config import get_ripl
from venture.test.config import on_inf_prim
from venture.test.config import rejectionSampling
from venture.test.config import skipWhenRejectionSampling
from venture.test.config import skipWhenSubSampling
from venture.test.stats import reportKnownDiscrete
from venture.test.stats import statisticalTest

############## (1) Test SymDirCat AAA

#
@gen_on_inf_prim("any")
def testMakeSymDirCat1():
  for maker in ["make_sym_dir_cat", "make_uc_sym_dir_cat"]:
    yield checkMakeSymDirCat1, maker

@statisticalTest
def checkMakeSymDirCat1(maker):
  """Extremely simple program, with an AAA procedure when uncollapsed"""
  ripl = get_ripl()
  ripl.assume("f", "(%s 1.0 2)" % maker)
  ripl.predict("(f)", label="pid")
  predictions = collectSamples(ripl, "pid")
  ans = [(0, .5), (1, .5)]
  return reportKnownDiscrete(ans, predictions)

@gen_on_inf_prim("any")
def testMakeSymDirCatAAA():
  for maker in ["make_sym_dir_cat", "make_uc_sym_dir_cat"]:
    yield checkMakeSymDirCatAAA, maker

@statisticalTest
def checkMakeSymDirCatAAA(maker):
  """Simplest program with collapsed AAA"""
  ripl = get_ripl()

  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "(%s a 4)" % maker)
  ripl.predict("(f)", label="pid")
  return checkDirichletCategoricalAAA(ripl, "pid")

@gen_on_inf_prim("any")
def testMakeSymDirCatFlip():
  """AAA where the SP flips between collapsed and uncollapsed."""
  for maker_1 in ["make_sym_dir_cat", "make_uc_sym_dir_cat"]:
    for maker_2 in ["make_sym_dir_cat", "make_uc_sym_dir_cat"]:
      yield checkMakeSymDirCatFlip, maker_1, maker_2

@skipWhenRejectionSampling("Observes resimulations of unknown code")
@skipWhenSubSampling(
  "The current implementation of subsampling can't handle this scaffold shape")
@statisticalTest
def checkMakeSymDirCatFlip(maker_1, maker_2):
  ripl = get_ripl()

  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "((if (lt a 10) %s %s) a 4)" % (maker_1, maker_2))
  ripl.predict("(f)", label="pid")
  return checkDirichletCategoricalAAA(ripl, "pid")

@gen_on_inf_prim("any")
def testMakeSymDirCatBrushObserves():
  """AAA where the SP flips between collapsed and uncollapsed, and
     there are observations in the brush."""
  for maker_1 in ["make_sym_dir_cat", "make_uc_sym_dir_cat"]:
    for maker_2 in ["make_sym_dir_cat", "make_uc_sym_dir_cat"]:
      yield checkMakeSymDirCatBrushObserves, maker_1, maker_2

@skipWhenRejectionSampling("Observes resimulations of unknown code")
@skipWhenSubSampling(
  "The current implementation of subsampling can't handle this scaffold shape")
@statisticalTest
def checkMakeSymDirCatBrushObserves(maker_1, maker_2):
  ripl = get_ripl()

  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "((if (lt a 10) %s %s) a 2)" % (maker_1, maker_2))
  ripl.predict("(f)", label="pid")

  return checkDirichletCategoricalBrush(ripl, "pid")

@skipWhenRejectionSampling("Observes resimulations of unknown code")
@skipWhenSubSampling(
  "The current implementation of subsampling can't handle this scaffold shape")
@statisticalTest
@on_inf_prim("any")
def testMakeSymDirCatNative():
  """AAA where the SP flips between collapsed, uncollapsed, and native"""
  ripl = get_ripl()

  ripl.assume("a", "(normal 10.0 1.0)")
# Might be collapsed, uncollapsed, or uncollapsed in Venture
  ripl.assume("f", """
((if (lt a 9.5)
     make_sym_dir_cat
     (if (lt a 10.5)
         make_uc_sym_dir_cat
         (lambda (alpha k)
           ((lambda (theta) (lambda () (categorical theta)))
            (symmetric_dirichlet alpha k)))))
 a 4)
""")
  ripl.predict("(f)", label="pid")
  return checkDirichletCategoricalAAA(ripl, "pid")

@gen_on_inf_prim("any")
def testMakeSymDirCatAppControlsFlip():
  for maker_1 in ["make_sym_dir_cat", "make_uc_sym_dir_cat"]:
    for maker_2 in ["make_sym_dir_cat", "make_uc_sym_dir_cat"]:
      yield checkMakeSymDirCatAppControlsFlip, maker_1, maker_2

@skipWhenRejectionSampling(
  "Too slow.  Is the log density of data bound too conservative?")
@statisticalTest
def checkMakeSymDirCatAppControlsFlip(maker_1, maker_2):
  """Two AAA SPs with same parameters, where their applications control
which are applied"""
  ripl = get_ripl()

  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "(%s a 4)" % maker_1)
  ripl.assume("g", "(%s a 4)" % maker_2)
  ripl.predict("(f)", label="pid")
  ripl.predict("(g)")
  for _ in range(5): ripl.observe("(g)", "integer<1>")
  ripl.predict("(if (eq (f) integer<1>) (g) (g))")
  ripl.predict("(if (eq (g) integer<1>) (f) (f))")
  return checkDirichletCategoricalAAA(ripl, "pid", infer="mixes_slowly")

@gen_on_inf_prim("any")
def testMakeDirCat1():
  for maker in ["make_dir_cat", "make_uc_dir_cat"]:
    yield checkMakeDirCat1, maker

@statisticalTest
def checkMakeDirCat1(maker):
  if rejectionSampling() and maker == "make_dir_cat":
    raise SkipTest("Is the log density of data bounded for "
                   "collapsed beta bernoulli?  Issue: "
                   "https://app.asana.com/0/9277419963067/10623454782852")
  ripl = get_ripl()

  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "(%s (array a a a a))" % maker)
  ripl.predict("(f)", label="pid")
  return checkDirichletCategoricalAAA(ripl, "pid")

@gen_on_inf_prim("any")
def testMakeSymDirCatWeakPrior():
  for maker in ["make_sym_dir_cat", "make_uc_sym_dir_cat"]:
    yield checkMakeSymDirCatWeakPrior, maker

@statisticalTest
def checkMakeSymDirCatWeakPrior(maker):
  ripl = get_ripl()

  ripl.assume("a", "1.0")
  ripl.assume("f", "(%s a 2)" % maker)
  ripl.predict("(f)", label="pid")

  return checkDirichletCategoricalWeakPrior(ripl, "pid")

@gen_on_inf_prim("none")
@gen_broken_in("puma", "Puma doesn't support the specified-objects form "
               "of dirichlet categorical.  Issue #340.")
def testDirCatInvalidOutput():
  for maker in ["(make_dir_cat (array 1 1) x)",
                "(make_sym_dir_cat 1 2 x)",
                "(make_uc_dir_cat (array 1 1) x)",
                "(make_uc_sym_dir_cat 1 2 x)"]:
    yield checkDirCatInvalidOutput, maker

def checkDirCatInvalidOutput(maker_form):
  raise SkipTest("Currently broken.  Issue #451.")
  r = get_ripl()
  r.assume("x1", "(flip)")
  r.assume("x2", "(flip)")
  r.infer("(force x1 true)")
  r.infer("(force x2 true)")
  r.assume("x", "(array x1 x2)")
  r.assume("f", maker_form)
  r.observe("(f)", "false")
  eq_([float("-inf")], r.infer("particle_log_weights"))

@gen_on_inf_prim("any")
@gen_broken_in("puma", "Puma doesn't support the specified-objects form "
               "of dirichlet categorical.  Issue #340.")
@gen_broken_in("lite", "Inference runs afoul of Issue #451.")
def testDirCatObjectVariation():
  for maker in ["(make_dir_cat (array 1 1) x)",
                "(make_sym_dir_cat 1 2 x)",
                "(make_uc_dir_cat (array 1 1) x)",
                "(make_uc_sym_dir_cat 1 2 x)"]:
    yield checkDirCatObjectVariation, maker

@statisticalTest
def checkDirCatObjectVariation(maker_form):
  "Testing for Issue #452."
  r = get_ripl()
  r.assume("x1", "(flip)")
  r.assume("x2", "(flip)")
  r.assume("x", "(array x1 x2)")
  r.assume("f", maker_form)
  r.observe("(f)", "true")
  r.observe("(f)", "true")
  r.observe("(f)", "true")
  predictions = collectSamples(r, "x", infer="mixes_slowly")
  ans = [([True,  True],  1),
         ([True,  False], 0.25),
         ([False, True],  0.25),
         ([False, False], 0),
       ]
  return reportKnownDiscrete(ans, predictions)

#### (2) Staleness

# This section should not hope to find staleness, since all backends should
# assert that a makerNode has been regenerated before applying it.
# Therefore this section should try to trigger that assertion.

@on_inf_prim("any")
@statisticalTest
def testStaleAAA_MSP():
  ripl = get_ripl()

  ripl.assume("a", "1.0")
  ripl.assume("f", "(make_uc_sym_dir_cat a 2)")
  ripl.assume("g", "(mem f)")
  ripl.assume("h", "g")
  ripl.predict("(h)", label="pid")

  return checkDirichletCategoricalWeakPrior(ripl, "pid")

@on_inf_prim("any")
@statisticalTest
def testStaleAAA_CSP():
  ripl = get_ripl()

  ripl.assume("a", "1.0")
  ripl.assume("f", "(make_uc_sym_dir_cat a 2)")
  ripl.assume("g", "(lambda () f)")
  ripl.assume("h", "(g)")
  ripl.predict("(h)", label="pid")

  return checkDirichletCategoricalWeakPrior(ripl, "pid")

@on_inf_prim("any")
@statisticalTest
@broken_in("puma",
           "Need to port records to Puma for references to work.  Issue #224")
def testStaleAAA_Madness():
  ripl = get_ripl()

  ripl.assume("a", "1.0")
  ripl.assume("f", "(make_uc_sym_dir_cat a 2)")
  ripl.assume("f2_maker", "(lambda () f)")
  ripl.assume("f2", "(f2_maker)")
  ripl.assume("xs", "(array (ref f) (ref f2))")
  ripl.assume("f3", "(deref (lookup xs 1))")
  ripl.assume("ys", """(dict (array (quote aaa) (quote bbb))
                             (array (ref f3) (ref f3)))""")
  ripl.assume("g", """(deref (if (flip) (lookup ys (quote aaa))
                                        (lookup ys (quote bbb))))""")
  ripl.predict("(g)", label="pid")

  return checkDirichletCategoricalWeakPrior(ripl, "pid")


#### Helpers

def checkDirichletCategoricalAAA(ripl, label, infer=None):
  for i in range(1, 4):
    for _ in range(default_num_data(20)):
      ripl.observe("(f)", "integer<%d>" % i)

  predictions = collectSamples(ripl, label, infer=infer)
  ans = [(0, .1), (1, .3), (2, .3), (3, .3)]
  return reportKnownDiscrete(ans, predictions)

def checkDirichletCategoricalBrush(ripl, label):
  for _ in range(default_num_data(10)): ripl.observe("(f)", "integer<1>")
  for _ in range(default_num_data(10)): ripl.observe("""
(if (lt a 10.0)
  (f)
  (f))""", "integer<1>")

  predictions = collectSamples(ripl, label)
  ans = [(0, .25), (1, .75)]
  return reportKnownDiscrete(ans, predictions)

def checkDirichletCategoricalWeakPrior(ripl, label):
  for _ in range(default_num_data(8)):
    ripl.observe("(f)", "integer<1>")

  predictions = collectSamples(ripl, label, infer="mixes_slowly")
  ans = [(1, .9), (0, .1)]
  return reportKnownDiscrete(ans, predictions)
