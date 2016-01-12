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

from venture.test.config import get_ripl

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
assume stan_sp = make_ven_stan(stan_prog, inputs, c_outputs);
predict stan_sp(7);
infer mh(default, one, 3);
"""
  r = get_ripl()
  r.set_mode("venture_script")
  r.execute_program(program)
