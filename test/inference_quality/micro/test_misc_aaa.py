# Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
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

from venture.test.stats import statisticalTest, reportKnownDiscrete
from venture.test.config import get_ripl, collectSamples, skipWhenRejectionSampling, rejectionSampling, skipWhenSubSampling, inParallel, gen_on_inf_prim

@gen_on_inf_prim("any")
def testMakeBetaBernoulli1():
  for maker in ["make_beta_bernoulli","make_uc_beta_bernoulli",
                "(lambda (a b) (let ((weight (beta a b))) (make_suff_stat_bernoulli weight)))"]:
    for hyper in ["10.0", "(normal 10.0 1.0)"]:
      yield checkMakeBetaBernoulli1, maker, hyper

@statisticalTest
def checkMakeBetaBernoulli1(maker, hyper):
  if rejectionSampling() and maker == "make_beta_bernoulli" and hyper == "(normal 10.0 1.0)":
    raise SkipTest("Is the log density of counts bounded for collapsed beta bernoulli?  Issue: https://app.asana.com/0/9277419963067/10623454782852")
  if inParallel() and "make_suff_stat_bernoulli" in maker and config["get_ripl"] == "puma":
    raise SkipTest("The Lite SPs in Puma interface is not thread-safe, and make_suff_stat_bernoulli comes from Lite.")
  ripl = get_ripl()

  ripl.assume("a", hyper)
  ripl.assume("f", "(%s a a)" % maker)
  ripl.predict("(f)", label="pid")

  for _ in range(20): ripl.observe("(f)", "true")

  predictions = collectSamples(ripl,"pid")
  ans = [(False,.25), (True,.75)]
  return reportKnownDiscrete(ans, predictions)

@gen_on_inf_prim("any")
def testMakeBetaBernoulli2():
  for maker in ["make_beta_bernoulli","make_uc_beta_bernoulli",
                "(lambda (a b) (let ((weight (beta a b))) (make_suff_stat_bernoulli weight)))"]:
    yield checkMakeBetaBernoulli2,maker

# These three represent mechanisable ways of fuzzing a program for
# testing language feature interactions (in this case AAA with
# constraint forwarding and brush).
@statisticalTest
def checkMakeBetaBernoulli2(maker):
  if rejectionSampling() and maker == "make_beta_bernoulli":
    raise SkipTest("Is the log density of counts bounded for collapsed beta bernoulli?  Issue: https://app.asana.com/0/9277419963067/10623454782852")
  if inParallel() and "make_suff_stat_bernoulli" in maker and config["get_ripl"] == "puma":
    raise SkipTest("The Lite SPs in Puma interface is not thread-safe, and make_suff_stat_bernoulli comes from Lite.")
  ripl = get_ripl()

  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "((lambda () (%s ((lambda () a)) ((lambda () a)))))" % maker)
  ripl.predict("(f)", label="pid")

  for _ in range(20): ripl.observe("((lambda () (f)))", "true")

  predictions = collectSamples(ripl,"pid")
  ans = [(False,.25), (True,.75)]
  return reportKnownDiscrete(ans, predictions)

@gen_on_inf_prim("any")
def testMakeBetaBernoulli3():
  for maker in ["make_beta_bernoulli","make_uc_beta_bernoulli",
                "(lambda (a b) (let ((weight (beta a b))) (make_suff_stat_bernoulli weight)))"]:
    yield checkMakeBetaBernoulli3,maker

@skipWhenRejectionSampling("Rejection sampling doesn't work when resimulations of unknown code are observed")
@skipWhenSubSampling("Leads to a scaffold structure that the current implementation of subsampling can't handle")
@statisticalTest
def checkMakeBetaBernoulli3(maker):
  if inParallel() and "make_suff_stat_bernoulli" in maker and config["get_ripl"] == "puma":
    raise SkipTest("The Lite SPs in Puma interface is not thread-safe, and make_suff_stat_bernoulli comes from Lite.")
  ripl = get_ripl()

  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "(%s a a)" % maker)
  ripl.predict("(f)", label="pid")

  for _ in range(10): ripl.observe("(f)", "true")
  for _ in range(10): ripl.observe("""
(if (lt a 10.0)
  (f)
  (f))""", "true")

  predictions = collectSamples(ripl,"pid")
  ans = [(False,.25), (True,.75)]
  return reportKnownDiscrete(ans, predictions)

@gen_on_inf_prim("any")
def testMakeBetaBernoulli4():
  for maker in ["make_beta_bernoulli","make_uc_beta_bernoulli",
                "(lambda (a b) (let ((weight (beta a b))) (make_suff_stat_bernoulli weight)))"]:
    yield checkMakeBetaBernoulli4,maker

@skipWhenRejectionSampling("Rejection sampling doesn't work when resimulations of unknown code are observed")
@skipWhenSubSampling("Leads to a scaffold structure that the current implementation of subsampling can't handle")
@statisticalTest
def checkMakeBetaBernoulli4(maker):
  if inParallel() and "make_suff_stat_bernoulli" in maker and config["get_ripl"] == "puma":
    raise SkipTest("The Lite SPs in Puma interface is not thread-safe, and make_suff_stat_bernoulli comes from Lite.")
  ripl = get_ripl()

  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", """
(if (lt a 10.0)
  ({0} a a)
  ({0} a a))""".format(maker))
  ripl.predict("(f)", label="pid")

  for _ in range(20): ripl.observe("(f)", "true")

  predictions = collectSamples(ripl,"pid")
  ans = [(False,.25), (True,.75)]
  return reportKnownDiscrete(ans, predictions)

@gen_on_inf_prim("resample")
def testAAAParticleWeights():
  for sp in ["(make_beta_bernoulli a a)",
             "(make_uc_beta_bernoulli a a)",
             "(let ((weight (beta a a))) (make_suff_stat_bernoulli weight))",
             "(make_dir_mult (array a a) (array true false))",
             "(make_uc_dir_mult (array a a) (array true false))",
             "(make_sym_dir_mult a 2 (array true false))",
             "(make_uc_sym_dir_mult a 2 (array true false))",
            ]:
    yield checkAAAParticleWeights, sp

@statisticalTest
def checkAAAParticleWeights(sp):
  if inParallel() and "make_suff_stat_bernoulli" in sp and config["get_ripl"] == "puma":
    raise SkipTest("The Lite SPs in Puma interface is not thread-safe, and make_suff_stat_bernoulli comes from Lite.")
  if "make_suff_stat_bernoulli" in sp and config["get_ripl"] == "puma":
    raise SkipTest("Now this mysteriously gives 'VentureTypeError: Invalid type \"sp\"'")
  if "dir_mult" in sp and config['get_ripl'] == 'puma':
    raise SkipTest("Dirichlet multinomial in Puma does not accept objects parameter.  Issue #340")
  ripl = get_ripl()

  ripl.assume("a", "1.0")
  # bogus labelled directives, so the infer step can forget them
  ripl.predict("nil", label="f")
  ripl.predict("nil", label="pid")

  predictions = collectSamples(ripl,"pid",infer="""\
(do (resample 10)
    (forget 'pid)
    (forget 'f)
    (assume f %s f)
    (predict (f) pid)
    (observe (f) true obs1)
    (observe (f) true obs2)
    (resample 1)
    (forget 'obs2)
    (forget 'obs1))""" % sp)
  ans = [(False,.25), (True,.75)]
  return reportKnownDiscrete(ans, predictions)
