# Copyright (c) 2015 MIT Probabilistic Computing Project.
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

import numpy as np

from venture.test.config import default_num_samples
from venture.test.config import default_num_transitions_per_sample
from venture.test.config import gen_on_inf_prim
from venture.test.config import get_ripl, collectIidSamples
from venture.test.stats import reportSameContinuous
from venture.test.stats import reportSameDiscrete
from venture.test.stats import statisticalTest
import venture.value.dicts as v

# Conjugate distributions participate in several useful relationships
# that we can take advantage of to test that they were implemented
# correctly.

# - For all hyper-parameter values and all data series lengths,
#   iterated collapsed sampling should produce the same distribution
#   on series as the foreign uncollapsed version, and the in-Venture
#   uncollapsed version.
#   - This is generateSimulationAgreementChecks, checking agreement on
#     a couple marginal distributions and a couple combinations of
#     2-item marginals.
#   - This exercises sampling and aux updating.

# - For all pairs of parameter values and all data sets, the suff stat
#   version should produce the same assessment ratio as the in-Venture
#   uncollapsed version.  In some cases, the exact assessment should
#   also be equal, if the suff stat program is coded to return the
#   probability of the sequence (when that is even computable from the
#   sufficient statistic).
#   - This is generateAssessmentAgreementChecks
#   - This exercises aux updating and assessment (of the suff stat version)

# - The Gibbs sampler for the foreign uncollapsed version can be
#   Geweke tested against its maker's simulation and made simulation.
#   - This is checkUCKernel
#   - This exercises the LKernel

def extract_sample(maker, params, index):
  r = get_ripl()
  r.assume("maker", maker)
  expr = v.app(v.sym("list"), *[v.app(v.sym("made")) for _ in range(index+1)])
  def one_sample():
    r.assume("made", v.app(v.sym("maker"), *params))
    ans = r.sample(expr)[-1]
    r.forget("made")
    return ans
  results = [one_sample() for _ in range(default_num_samples(5))]
  return results

def extract_cross_sample(maker, params, index1, index2, combiner):
  r = get_ripl()
  r.assume("maker", maker)
  index = max(index1, index2)
  expr = v.app(v.sym("list"), *[v.app(v.sym("made")) for _ in range(index+1)])
  def one_sample():
    r.assume("made", v.app(v.sym("maker"), *params))
    vec = r.sample(expr)
    r.forget("made")
    return combiner(vec[index1], vec[index2])
  results = [one_sample() for _ in range(default_num_samples(5))]
  return results

@statisticalTest
def checkSameMarginal(name, maker2, params, index):
  package = simulation_agreement_packages[name]
  native = package['native']
  report = package['reporter']
  return report(extract_sample(native, params, index),
                extract_sample(maker2, params, index))

@statisticalTest
def checkSameCross(name, maker2, params, index1, index2):
  package = simulation_agreement_packages[name]
  native = package['native']
  report = package['reporter']
  combiner = package['combiner']
  one = extract_cross_sample(native, params, index1, index2, combiner)
  other = extract_cross_sample(maker2, params, index1, index2, combiner)
  return report(one, other)

native_nig_normal = """(lambda (m V a b)
  (let ((variance (inv_gamma a b))
        (mean (normal m (sqrt (* V variance))))
        (stddev (sqrt variance)))
    (lambda () (normal mean stddev))))"""

suff_stat_nig_normal = """(lambda (m V a b)
  (let ((variance (inv_gamma a b))
        (mean (normal m (sqrt (* V variance))))
        (stddev (sqrt variance)))
    (make_suff_stat_normal mean stddev)))"""

native_beta_bernoulli = """(lambda (al be)
  (let ((weight (beta al be)))
    (lambda () (bernoulli weight))))"""

suff_stat_beta_bernoulli = """(lambda (al be)
  (let ((weight (beta al be)))
    (make_suff_stat_bernoulli weight)))"""

native_dir_mult = """(lambda (alphas)
  (let ((weights (dirichlet alphas)))
    (lambda () (categorical weights))))"""

native_sym_dir_mult = """(lambda (alpha n)
  (let ((weights (symmetric_dirichlet alpha n)))
    (lambda () (categorical weights))))"""

native_gamma_poisson = """(lambda (alpha beta)
  (let ((rate (gamma alpha beta)))
    (lambda () (poisson rate))))"""

suff_stat_gamma_poisson = """(lambda (alpha beta)
  (let ((rate (gamma alpha beta)))
    (make_suff_stat_poisson rate)))"""

simulation_agreement_packages = {
  'nig_normal' : {
    'native' : native_nig_normal,
    'optimized' : ['make_nig_normal', 'make_uc_nig_normal',
                   suff_stat_nig_normal],
    'gibbs' : 'make_uc_nig_normal',
    'param_sets' : [(1.0, 1.0, 1.0, 1.0),
                    (2.0, 3.0, 4.0, 5.0)],
    'reporter' : reportSameContinuous,
    'combiner' : lambda x, y: x*y
  },
  'beta_bernoulli' : {
    'native' : native_beta_bernoulli,
    'optimized' : ['make_beta_bernoulli', 'make_uc_beta_bernoulli',
                   suff_stat_beta_bernoulli],
    'gibbs' : 'make_uc_beta_bernoulli',
    'param_sets' : [(1.0, 1.0),
                    (2.0, 3.0)],
    'reporter' : reportSameDiscrete,
    'combiner' : lambda x, y: (x,y)
  },
  'dir_mult' : {
    'native' : native_dir_mult,
    'optimized' : ['make_dir_mult', 'make_uc_dir_mult'],
    'gibbs' : 'make_uc_dir_mult',
    'param_sets' : [(v.app("array", 0.5, 0.5, 0.5),),
                    (v.app("array", 0.2, 0.2, 0.2, 0.2, 0.2),)],
    'reporter' : reportSameDiscrete,
    'combiner' : lambda x, y: (x,y),
  },
  'sym_dir_mult' : {
    'native' : native_sym_dir_mult,
    'optimized' : ['make_sym_dir_mult', 'make_uc_sym_dir_mult'],
    'gibbs' : 'make_uc_sym_dir_mult',
    'param_sets' : [(0.5, 4), (0.2, 8)],
    'reporter' : reportSameDiscrete,
    'combiner' : lambda x, y: (x,y),
  },
  'gamma_poisson' : {
    'native' : native_gamma_poisson,
    'optimized' : ['make_gamma_poisson', 'make_uc_gamma_poisson',
                   suff_stat_gamma_poisson],
    'gibbs' : 'make_uc_gamma_poisson',
    'param_sets' : [(1.0, 1.0), (4.0, 1.5)],
    'reporter' : reportSameDiscrete,
    'combiner' : lambda x, y: (x,y)
  },
}

def generateSimulationAgreementChecks(name):
  package = simulation_agreement_packages[name]
  for maker in package['optimized']:
    for params in package['param_sets']:
      for index in [0, 10]:
        yield checkSameMarginal, name, maker, params, index
      for index1, index2 in [(1,2), (3,7)]:
        yield checkSameCross, name, maker, params, index1, index2

@gen_on_inf_prim("none")
def testNigNormalSimulationAgreement():
  for c in generateSimulationAgreementChecks('nig_normal'):
    yield c

@gen_on_inf_prim("none")
def testBetaBernoulliSimulationAgreement():
  for c in generateSimulationAgreementChecks('beta_bernoulli'):
    yield c

@gen_on_inf_prim("none")
def testDirMultSimulationAgreement():
  for c in generateSimulationAgreementChecks('dir_mult'):
    yield c

@gen_on_inf_prim("none")
def testSymDirMultSimulationAgreement():
  for c in generateSimulationAgreementChecks('sym_dir_mult'):
    yield c

@gen_on_inf_prim("none")
def testGamPosSimulationAgreement():
  for c in generateSimulationAgreementChecks('gamma_poisson'):
    yield c

def extract_assessment(maker, params, data):
  r = get_ripl()
  r.assume("maker", maker)
  r.assume("made",
           v.app(v.sym("maker"),
                 *[v.app(v.sym("exactly"), p) for p in params]))
  for item in data:
    r.observe("(made)", item)
  ans = r.infer("global_log_likelihood")
  return ans

def checkSameAssessment(name, params, data):
  native = same_assessment_packages[name]['native']
  maker = same_assessment_packages[name]['optimized']
  assert np.allclose(extract_assessment(native, params, data),
                     extract_assessment(maker, params, data))

def checkSameAssessmentRatio(name, params1, params2, data):
  native = same_assessment_packages[name]['native']
  maker = same_assessment_packages[name]['optimized']
  n1s = extract_assessment(native, params1, data)
  n2s = extract_assessment(native, params2, data)
  o1s = extract_assessment(maker, params1, data)
  o2s = extract_assessment(maker, params2, data)
  assert np.allclose([n1 - n2 for n1, n2 in zip(n1s, n2s)],
                     [o1 - o2 for o1, o2 in zip(o1s, o2s)])

frob = \
[-1.81, -1.62, -1.53, -1.35, -1.02, -0.85, -0.69, -0.65, -0.55, -0.48,
 -0.39, -0.28, -0.20, -0.18, -0.16, -0.03, 0.02, 0.06, 0.07, 0.19,
 0.22, 0.27, 0.31, 0.39, 0.46, 0.50, 0.52, 0.56, 0.57, 0.60,
 0.60, 0.61, 0.63, 0.70, 0.70, 0.74, 0.76, 0.78, 0.80, 0.85,
 0.90, 0.92, 0.94, 0.96, 1.00, 1.06, 1.12, 1.17, 1.21, 1.23,
 1.25, 1.27, 1.28, 1.31, 1.35, 1.37, 1.40, 1.43, 1.47, 1.48,
 1.49, 1.53, 1.53, 1.55, 1.62, 1.67, 1.74, 1.76, 1.78, 1.80,
 1.83, 1.87, 1.89, 1.92, 2.03, 2.07, 2.10, 2.12, 2.14, 2.19,
 2.25, 2.27, 2.29, 2.43, 2.52, 2.57, 2.59, 2.65, 2.70, 2.71,
 2.75, 2.80, 2.84, 3.03, 3.20, 3.37, 3.50, 3.58, 3.76, 4.16, 4.34]

native_fixed_normal = """(lambda (mu sigma)
  (lambda () (normal mu sigma)))"""

native_fixed_bernoulli = """(lambda (weight)
  (lambda () (bernoulli weight)))"""

native_fixed_poisson = """(lambda (rate)
  (lambda () (poisson rate)))"""

same_assessment_packages = {
  'normal' : {
    'native' : native_fixed_normal,
    'optimized' : 'make_suff_stat_normal',
    'param_sets' : [(0.0, 1.0),
                    (2.0, 3.0),
                    (-2.0, 30.0),
                    (5.0, 0.1),
                  ],
    'datasets' : [[0.0],
                  map(float, range(10)),
                  frob]
  },
  'bernoulli' : {
    'native' : native_fixed_bernoulli,
    'optimized' : 'make_suff_stat_bernoulli',
    'param_sets' : [(0.1,), (0.3,), (0.5,), (0.7,), (0.9,)],
    'datasets' : [[True],
                  [False] * 10,
                  [True, False, True] * 5],
  },
  'poisson' : {
    'native' : native_fixed_poisson,
    'optimized' : 'make_suff_stat_poisson',
    'param_sets' : [(0.1,), (0.3,), (0.5,), (0.9,)],
    'datasets' : [[1.0],
                  [7.0] * 10,
                  [2.0, 3.0, 5.0] * 5],
    # make_suff_stat_poisson assesses the probability of its
    # statistics, not the sequence that produced them, because, unlike
    # with many other distributions, the probability of the sequence
    # is not uniquely determined.  This is ok, though: assessment
    # differences will still be the same as with the native version.
    'ratio_only' : True
  },
}

def generateAssessmentAgreementChecks(name):
  package = same_assessment_packages[name]
  for params in package['param_sets']:
    for dataset in package['datasets']:
      if 'ratio_only' in package and package['ratio_only']:
        for params2 in package['param_sets']:
          yield checkSameAssessmentRatio, name, params, params2, dataset
      else:
        yield checkSameAssessment, name, params, dataset

@gen_on_inf_prim("none")
def testNormalSuffStatsAssessmentAgreement():
  for c in generateAssessmentAgreementChecks('normal'):
    yield c

@gen_on_inf_prim("none")
def testBernoulliSuffStatsAssessmentAgreement():
  for c in generateAssessmentAgreementChecks('bernoulli'):
    yield c

@gen_on_inf_prim("none")
def testPoissonSuffStatsAssessmentAgreement():
  for c in generateAssessmentAgreementChecks('poisson'):
    yield c

@statisticalTest
def checkUCKernel(name, params):
  package = simulation_agreement_packages[name]
  maker = package['gibbs']
  def enstring(param):
    if isinstance(param, list):
      return "(" + " ".join(enstring(p) for p in param) + ")"
    else:
      return str(param)
  param_str = " ".join([enstring(p) for p in params])
  report = package['reporter']
  r = get_ripl()
  r.assume("made", "(tag 'latent 0 (%s %s))" % (maker, param_str))
  for i in range(5):
    r.predict("(tag 'data %d (made))" % i, label="datum_%d" % i)
  def samples(infer):
    return collectIidSamples(r, address="datum_0",
                             num_samples=default_num_samples(),
                             infer=infer)
  prior = samples("pass")
  geweke = """(repeat %d (do (mh 'latent one 1)
    (mh 'data all 1)))""" % default_num_transitions_per_sample()
  geweke_result = samples(geweke)
  return report(prior, geweke_result)

@gen_on_inf_prim("mh") # Really just the custom LKernel
def testNigNormalUCKernel():
  name = 'nig_normal'
  for params in simulation_agreement_packages[name]['param_sets']:
    yield checkUCKernel, name, params

@gen_on_inf_prim("mh") # Really just the custom LKernel
def testBetaBernoulliUCKernel():
  name = 'beta_bernoulli'
  for params in simulation_agreement_packages[name]['param_sets']:
    yield checkUCKernel, name, params

@gen_on_inf_prim("mh") # Really just the custom LKernel
def testDirMultUCKernel():
  name = 'dir_mult'
  for params in simulation_agreement_packages[name]['param_sets']:
    yield checkUCKernel, name, params

@gen_on_inf_prim("mh") # Really just the custom LKernel
def testSymDirMultUCKernel():
  name = 'sym_dir_mult'
  for params in simulation_agreement_packages[name]['param_sets']:
    yield checkUCKernel, name, params

@gen_on_inf_prim("mh") # Really just the custom LKernel
def testGamPosUCKernel():
  name = 'gamma_poisson'
  for params in simulation_agreement_packages[name]['param_sets']:
    yield checkUCKernel, name, params
