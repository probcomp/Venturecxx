# Copyright (c) 2015, 2016 MIT Probabilistic Computing Project.
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

import math
import os.path

from nose.tools import eq_
import scipy.stats as stats

from venture.test.config import broken_in
from venture.test.config import collectSamples
from venture.test.config import get_ripl
from venture.test.config import needs_pystan
from venture.test.stats import reportKnownGaussian
from venture.test.stats import statisticalTest

this_dir = os.path.dirname(os.path.abspath(__file__))
cache_dir = os.path.join(this_dir, "models")

@needs_pystan
@broken_in('puma', "https://github.com/probcomp/Venturecxx/issues/329")
def testSmoke():
  program = """
infer load_plugin("venstan.py");
assume stan_prog = "
data {
  int N;
  real y[N];
}
parameters {
  real mu;
  real<lower=0> sigma;
}
model {
  y ~ normal(mu, sigma);
}
generated quantities {
  real y_out[N];
  for (n in 1:N)
    y_out[n] <- normal_rng(mu, sigma);
}";
assume inputs = quote("N"("Int")());
assume c_outputs = quote("y_out"("y", "UArray(Number)", "N")());
assume stan_sp = make_ven_stan(stan_prog, inputs, c_outputs, "%s");
predict stan_sp(7);
infer mh(default, one, 3);
""" % cache_dir
  r = get_ripl()
  r.set_mode("venture_script")
  r.execute_program(program)

@needs_pystan
@broken_in('puma', "https://github.com/probcomp/Venturecxx/issues/329")
def testSmokeChurchPrime():
  program = """
(load_plugin "venstan.py")
(assume stan_prog "
data {
  int N;
  real y[N];
}
parameters {
  real mu;
  real<lower=0> sigma;
}
model {
  y ~ normal(mu, sigma);
}
generated quantities {
  real y_out[N];
  for (n in 1:N)
    y_out[n] <- normal_rng(mu, sigma);
}")
(assume inputs '(("N" "Int")))
(assume c_outputs '(("y_out" "y" "UArray(Number)" "N")))
(assume stan_sp (make_ven_stan stan_prog inputs c_outputs "%s"))
(predict (stan_sp 7))
(mh default one 3)
""" % cache_dir
  r = get_ripl()
  r.set_mode("church_prime")
  r.execute_program(program)

normal_in_stan_snippet = """
(load_plugin "venstan.py")
(assume stan_prog "
data {
  real mu;
  real<lower=0> sigma;
  real y;
}
parameters {
  real<lower=0, upper=1> bogon;
}
model {
  increment_log_prob(normal_log(y, mu, sigma));
}
generated quantities {
  real y_out;
  y_out <- normal_rng(mu, sigma);
}")
(assume inputs '(("mu" "Number") ("sigma" "Number")))
(assume c_outputs '(("y_out" "y" "Number")))
(assume stan_normal (make_ven_stan stan_prog inputs c_outputs "%s"))""" % \
  (cache_dir,)

@needs_pystan
@broken_in('puma', "https://github.com/probcomp/Venturecxx/issues/329")
def testReportedPosterior():
  r = get_ripl()
  r.execute_program(normal_in_stan_snippet)
  eq_(stats.norm.logpdf(1, loc=0, scale=1), r.observe("(stan_normal 0 1)", 1))

@needs_pystan
@broken_in('puma', "https://github.com/probcomp/Venturecxx/issues/329")
@statisticalTest
def testInference(seed):
  r = get_ripl(seed=seed)
  r.execute_program(normal_in_stan_snippet)
  r.execute_program("""
(assume x (normal 0 1))
(observe (stan_normal x 1) 2)""")
  predictions = collectSamples(r, "x")
  return reportKnownGaussian(1, math.sqrt(0.5), predictions)
