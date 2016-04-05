# Copyright (c) 2014, 2015, 2016 MIT Probabilistic Computing Project.
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
from testconfig import config

from venture.test.config import collectSamples
from venture.test.config import default_num_samples
from venture.test.config import default_num_transitions_per_sample
from venture.test.config import gen_on_inf_prim
from venture.test.config import get_ripl
from venture.test.config import on_inf_prim
from venture.test.stats import reportKnownDiscrete
from venture.test.stats import reportSameDiscrete
from venture.test.stats import statisticalTest

@gen_on_inf_prim("gibbs")
def testEnumerativeGibbsBasic1():
  yield checkEnumerativeGibbsBasic1, "false"
  yield checkEnumerativeGibbsBasic1, "true"

@statisticalTest
def checkEnumerativeGibbsBasic1(in_parallel):
  """Basic sanity test"""
  ripl = get_ripl()
  ripl.predict("(bernoulli)", label="pid")
  infer = "(gibbs default one %s %s)" % \
      (default_num_transitions_per_sample(), in_parallel)

  predictions = collectSamples(ripl, "pid", infer=infer)
  ans = [(True, .5), (False, .5)]
  return reportKnownDiscrete(ans, predictions)

@gen_on_inf_prim("gibbs")
def testEnumerativeGibbsBasic2():
  yield checkEnumerativeGibbsBasic2, "false"
  yield checkEnumerativeGibbsBasic2, "true"

@statisticalTest
def checkEnumerativeGibbsBasic2(in_parallel):
  """Basic sanity test"""
  ripl = get_ripl()
  ripl.assume("x", "(flip 0.1)", label="pid")
  infer = "(gibbs default one %s %s)" % \
      (default_num_transitions_per_sample(), in_parallel)
  predictions = collectSamples(ripl, "pid", infer=infer)
  ans = [(False, .9), (True, .1)]
  return reportKnownDiscrete(ans, predictions)

@gen_on_inf_prim("gibbs")
def testEnumerativeGibbsGotcha():
  yield checkEnumerativeGibbsGotcha, "false"
  yield checkEnumerativeGibbsGotcha, "true"

def checkEnumerativeGibbsGotcha(in_parallel):
  """Enumeration should not break on things that look like they're in
the support but aren't."""
  ripl = get_ripl()
  ripl.predict("(bernoulli 1)")
  ripl.predict("(bernoulli 0)")
  ripl.infer("(gibbs default one 1 %s)" % in_parallel)
  ripl.infer("(gibbs default all 1 %s)" % in_parallel)

@statisticalTest
@on_inf_prim("gibbs")
def testEnumerativeGibbsBoostThrashExact():
  """Enumerating two choices with the same posterior probability should
not thrash."""
  ripl = get_ripl()
  ripl.assume("x", "(flip 0.1)", label="pid")
  ripl.observe("(flip (if x .9 .1))", "true")
  predictions = collectSamples(ripl, "pid", infer="(gibbs default one 1)")
  ans = [(False, .5), (True, .5)]
  return reportKnownDiscrete(ans, predictions)

@gen_on_inf_prim("gibbs")
def testEnumerativeGibbsBoostThrashClose():
  yield checkEnumerativeGibbsBoostThrashClose, "false"
  yield checkEnumerativeGibbsBoostThrashClose, "true"

@statisticalTest
def checkEnumerativeGibbsBoostThrashClose(in_parallel):
  """Enumerating two choices with almost the same posterior probability
should mix well."""
  ripl = get_ripl()
  ripl.assume("x", "(flip 0.1)", label="pid")
  ripl.observe("(flip (if x .91 .09))", "true")
  infer = "(gibbs default one %s %s)" % \
      (default_num_transitions_per_sample(), in_parallel)
  predictions = collectSamples(ripl, "pid", infer=infer)
  ans = [(False, .471), (True, .529)]
  return reportKnownDiscrete(ans, predictions)

@statisticalTest
@on_inf_prim("gibbs")
def testEnumerativeGibbsCategorical1():
  """Tests mixing when the prior is far from the posterior."""
  ripl = get_ripl()
  ripl.assume('x', '(categorical (simplex 0.1 0.9) (array 0 1))', label="pid")
  ripl.observe('(flip (if (= x 0) 0.9 0.1))', "true")

  predictions = collectSamples(ripl, "pid", infer="(gibbs default all 1)")
  ans = [(False, .5), (True, .5)]
  return reportKnownDiscrete(ans, predictions)

@gen_on_inf_prim("gibbs")
def testEnumerativeGibbsXOR1():
  yield checkEnumerativeGibbsXOR1, "false"
  yield checkEnumerativeGibbsXOR1, "true"

@statisticalTest
def checkEnumerativeGibbsXOR1(in_parallel):
  """Tests that an XOR chain mixes with enumerative gibbs.
     Note that with RESET=True, this will seem to mix with MH.
     The next test accounts for that."""
  ripl = get_ripl()

  ripl.assume("x", "(tag 0 0 (bernoulli 0.001))", label="pid")
  ripl.assume("y", "(tag 0 0 (bernoulli 0.001))")
  ripl.assume("noisy_true", "(lambda (pred noise) (flip (if pred 1.0 noise)))")
  ripl.observe("(noisy_true (= (+ x y) 1) .000001)", "true")
  infer = "(gibbs 0 0 %s %s)" % \
      (default_num_transitions_per_sample(), in_parallel)
  predictions = collectSamples(ripl, "pid", infer=infer)
  ans = [(True, .5), (False, .5)]
  return reportKnownDiscrete(ans, predictions)

@gen_on_inf_prim("gibbs")
def testEnumerativeGibbsXOR2():
  yield checkEnumerativeGibbsXOR2, "false"
  yield checkEnumerativeGibbsXOR2, "true"

@statisticalTest
def checkEnumerativeGibbsXOR2(in_parallel):
  """Tests that an XOR chain mixes with enumerative gibbs."""
  ripl = get_ripl()

  ripl.assume("x", "(tag 0 0 (bernoulli 0.0015))", label="pid")
  ripl.assume("y", "(tag 0 0 (bernoulli 0.0005))")
  ripl.assume("noisy_true", "(lambda (pred noise) (flip (if pred 1.0 noise)))")
  ripl.observe("(noisy_true (= (+ x y) 1) .000001)", "true")
  infer = "(gibbs 0 0 %s %s)" % \
      (default_num_transitions_per_sample(), in_parallel)
  predictions = collectSamples(ripl, "pid", infer=infer)
  ans = [(True, .75), (False, .25)]
  return reportKnownDiscrete(ans, predictions)

@gen_on_inf_prim("gibbs")
def testEnumerativeGibbsXOR3():
  yield checkEnumerativeGibbsXOR3, "false"
  yield checkEnumerativeGibbsXOR3, "true"

@statisticalTest
def checkEnumerativeGibbsXOR3(in_parallel):
  """A regression catching a mysterious math domain error."""
  ripl = get_ripl()

  ripl.assume("x", "(tag 0 0 (bernoulli 0.0015))", label="pid")
  ripl.assume("y", "(tag 0 0 (bernoulli 0.0005))")
  ripl.assume("noisy_true",
              "(lambda (pred noise) (tag 0 0 (flip (if pred 1.0 noise))))")
  # This predict is the different between this test and
  # testEnumerativeGibbsXOR2, and currently causes a mystery math
  # domain error.

  ripl.predict("(noisy_true (= (+ x y) 1) .000001)")
  ripl.observe("(noisy_true (= (+ x y) 1) .000001)", "true")
  infer = "(gibbs 0 0 %s %s)" % \
      (default_num_transitions_per_sample(), in_parallel)
  predictions = collectSamples(ripl, "pid", infer=infer)
  ans = [(True, .75), (False, .25)]
  return reportKnownDiscrete(ans, predictions)

@statisticalTest
@on_inf_prim("gibbs") # Also rejection, but really testing Gibbs
def testEnumerativeGibbsBrushRandomness():
    """Test that Gibbs targets the correct stationary distribution, even
    when there may be random choices downstream of variables being
    enumerated.
    """
    ripl = get_ripl()
    ripl.assume("z", "(tag 'z 0 (flip))")
    ripl.assume("x", "(if z 0 (normal 0 10))")
    ripl.observe("(normal x 1)", "4")
    ripl.predict("z", label="pid")
    def posterior_inference_action():
      # Work around the fact that Puma doesn't have rejection sampling
      # by asking for a bunch of MH.
      if config['get_ripl'] == 'lite':
        return "(rejection default all 1)"
      else:
        return "(mh default one %d)" % (default_num_transitions_per_sample(),)
    ans = collectSamples(ripl, "pid", infer=posterior_inference_action())
    gibbs_inference_action = "(do %s (gibbs 'z 0 1))" % \
                             (posterior_inference_action(),)
    predictions = collectSamples(
      ripl, "pid", infer=gibbs_inference_action)
    return reportSameDiscrete(ans, predictions)

@statisticalTest
@on_inf_prim("gibbs")
def testEnumerateCoupledChoices1():
  # A test case for the first problem identified in Issue #462.
  #
  # If enumaration collects the candidate value sets all at once at
  # the beginning of the enumeration run, and if the set of options
  # for a later choice depends on the choice taken at an earlier one
  # (e.g., for the made SP of make_crp), trouble will ensue because we
  # need to compute a dependent rather than independent product.
  #
  # This example suffices to bring the problem into relief.  If a CRP
  # has only one extant table at the time enumeration is invoked,
  # (arranged by the force calls), each node will consider that table
  # and one new table as the only options.  Enumeration will therefore
  # consider 8 options, in none of which will all three nodes be
  # assigned to distinct tables.
  raise SkipTest("Fails due to https://github.com/probcomp/Venturecxx/issues/462")
  r = get_ripl()
  r.assume("crp", "(make_crp 1)")
  r.assume("result1", "(crp)")
  r.assume("result2", "(crp)")
  r.assume("result3", "(crp)")
  r.predict("(and (not (eq result1 result2))"
                 "(and (not (eq result2 result3))"
                      "(not (eq result1 result3))))", label="pid")
  ans = collectSamples(r, "pid", infer="reset_to_prior",
                       num_samples=default_num_samples(4))
  gibbs_from_same = """(do
    (force result1 atom<1>)
    (force result2 atom<1>)
    (force result3 atom<1>)
    (gibbs default all 1))"""
  # One step of Gibbs from any initial condition should move to the
  # posterior (which in this case equals the prior).
  predicts = collectSamples(r, "pid", infer=gibbs_from_same,
                            num_samples=default_num_samples(4))
  return reportSameDiscrete(ans, predicts)

@statisticalTest
@on_inf_prim("gibbs")
def testEnumerateCoupledChoices2():
  # A second illustration of Issue #462 (second manifestation).
  #
  # If enumeration computes the set of candidate values before
  # detaching, as an independent product, it will invent combinations
  # that are actually distinct representations of semantically the
  # same option.  Thus, even though all possibilities will (as in this
  # variant) be considered, some will be overweighted.
  #
  # Specifically, if the initial state is three calls to the same CRP
  # with distinct values (arranged by the force statements),
  # enumeration will invent 4^3 different combinations of tables to
  # try; whereas there are only 5 that differ up to renumbering of the
  # tables: (1, 1, 1), (1, 1, 2), (1, 2, 1), (1, 2, 2), and (1, 2, 3).
  # They cannot, therefore, be overrepresented evenly, and this leads
  # to the wrong posterior.
  raise SkipTest("Fails due to https://github.com/probcomp/Venturecxx/issues/462")
  r = get_ripl()
  r.assume("crp", "(make_crp 1)")
  r.assume("result1", "(crp)")
  r.assume("result2", "(crp)")
  r.assume("result3", "(crp)")
  r.predict("(and (not (eq result1 result2))"
                 "(and (not (eq result2 result3))"
                      "(not (eq result1 result3))))", label="pid")
  ans = collectSamples(r, "pid", infer="reset_to_prior",
                       num_samples=default_num_samples(4))
  gibbs_from_different = """(do
    (force result1 atom<1>)
    (force result2 atom<2>)
    (force result3 atom<3>)
    (gibbs default all 1))"""
  # One step of Gibbs from any initial condition should move to the
  # posterior (which in this case equals the prior).
  predicts = collectSamples(r, "pid", infer=gibbs_from_different,
                            num_samples=default_num_samples(4))
  return reportSameDiscrete(ans, predicts)

@statisticalTest
@on_inf_prim("gibbs")
def testEnumerateCoupledChoices3():
  # A third illustration of Issue #462 (second manifestation).
  #
  # Enumerating a single choice should not depend on the initial value
  # of that choice, but due to #462 it does.  The setup here is
  # enumerating one of two choices from a CRP.  If they are initially
  # distinct, enumeration will consider three options, the latter two
  # of which will be equivalent: "become the same as the other point",
  # "remain the same as I was", and "become a unique snowflake".  This
  # will cause it to overweight the state where the choices are
  # distinct by 2:1.
  raise SkipTest("Fails due to https://github.com/probcomp/Venturecxx/issues/462")
  r = get_ripl()
  r.assume("crp", "(make_crp 1)")
  r.assume("result1", "(crp)")
  r.assume("result2", "(crp)")
  r.predict("(eq result1 result2)", label="pid")
  gibbs_from_same = """(do
    (force result1 atom<1>)
    (force result2 atom<1>)
    (gibbs default one 1))"""
  ans = collectSamples(r, "pid", infer=gibbs_from_same,
                       num_samples=default_num_samples(6))
  gibbs_from_different = """(do
    (force result1 atom<1>)
    (force result2 atom<2>)
    (gibbs default one 1))"""
  # In this case, gibbs_from_same happens to compute the exact
  # posterior, which equals the prior, and is 50-50 on whether the
  # atoms are the same.
  predicts = collectSamples(r, "pid", infer=gibbs_from_different,
                            num_samples=default_num_samples(6))
  return reportSameDiscrete(ans, predicts)

@statisticalTest
@on_inf_prim("gibbs")
def testOccasionalRejection():
  # The mem is relevant: without it, the test passes even in Puma.
  r = get_ripl()
  r.execute_program("""
(assume cluster_id (flip))
(assume cluster (mem (lambda (id) (normal 0 1))))
(observe (cluster cluster_id) 1)
""")
  infer = "(do (force cluster_id true) (gibbs default one 1 false))"
  predictions = collectSamples(r, address="cluster_id", infer=infer)
  ans = [(True, 0.5), (False, 0.5)]
  return reportKnownDiscrete(ans, predictions)

@on_inf_prim("gibbs")
def testOccasionalRejectionScope():
  # Like the previous test but in a custom scope, because Lite
  # special-cases the default scope when computing the
  # number-of-blocks correction.
  # Note: This variant may not be very high power, because the "frob"
  # scope probably registers as always having two blocks, even though
  # one of them will, at runtime, end up having no unconstrained
  # random choices.
  r = get_ripl()
  r.execute_program("""
(assume cluster_id (tag "frob" 0 (flip)))
(assume cluster (mem (lambda (id) (tag "frob" 1 (normal 0 1)))))
(observe (cluster cluster_id) 1)
""")
  infer = '(do (force cluster_id true) (gibbs "frob" one 1 false))'
  predictions = collectSamples(r, address="cluster_id", infer=infer)
  ans = [(True, 0.5), (False, 0.5)]
  return reportKnownDiscrete(ans, predictions)

@statisticalTest
@on_inf_prim("gibbs")
def testOccasionalRejectionBrush():
  # Another version, this time with explicit brush creating the mix mh
  # correction.

  # Note that in this case, the correction is sound: The number of
  # random choices available in the default one scope really is
  # changing, whereas in `testOccasionalRejection` it is not.

  # To see why, consider what transition the operator (gibbs default
  # one 1) induces on this model (assuming the current behavior of
  # always claiming the proposal weight is 0).
  # - False, False is not possible
  # - From False, True:
  #   - With probability 50%, enumerate the second coin, and propose
  #     to keep it at True.
  #   - Else, enumerate the first coin, find that both states are
  #     equally good, and
  #     - With probability 50%, propose to leave it
  #     - Else, propose to change it to True, which is accepted (with
  #       or without the correction)
  #   - Ergo, move to the True state 25% of the time.
  # - From True, enumerate the first coin
  #   - With probability 50%, the second coin comes up False in the brush;
  #     propose to stay in the True state.
  #   - Else, both states equally good
  #     - With probability 50%, propose to stay in the True state
  #     - Else, propose to move to the False, True state
  #       - If the correction is applied, this proposal will be
  #         rejected with probability 50%.
  #   - Ergo, move to the False, True state 25% (no correction) or
  #     12.5% (correction) of the time.
  # - The former will induce a 50/50 stationary distribution on the
  #   value of flip1, whereas the right answer is 2:1 odds in favor of
  #   True.
  r = get_ripl()
  r.execute_program("""
(assume flip1 (flip))
(assume flip1_or_flip2
  (if flip1 true (flip)))
(observe (exactly flip1_or_flip2) true)
;; Crash with a non-negligible probability per transition in Puma
(gibbs default one 50 false)
""")
  infer = "(gibbs default one %s false)" % default_num_transitions_per_sample()
  predictions = collectSamples(r, address="flip1", infer=infer)
  ans = [(True, 2.0/3), (False, 1.0/3)]
  return reportKnownDiscrete(ans, predictions)
