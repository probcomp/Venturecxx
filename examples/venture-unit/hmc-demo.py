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

import scipy.stats
import numpy as np

from venture import shortcuts
import venture.unit as u
import venture.value.dicts as v

class HMCDemo(u.VentureUnit):
  def makeAssumes(self):
    program = """
[ASSUME x (tag (quote param) 0 (uniform_continuous -4 4))]
[ASSUME y (tag (quote param) 1 (uniform_continuous -4 4))]
[ASSUME xout (if (< x 0)
    (normal x 0.5)
    (normal x 4))]
[ASSUME out (multivariate_normal
  (array xout y) (matrix (list (list 1 0.5) (list 0.5 1))))]
"""
    commands = [command_str.split("]")[0].split(" ", 1)
                for command_str in program.strip().split("[ASSUME ") if command_str]
    for (var, exp) in commands:
      self.assume(var, exp)

  def makeObserves(self):
    self.observe("out", v.list([v.real(0), v.real(0)]))

# int_R pdf(xout|x) pdf([0,0]|[xout, y])
def true_pdf(x, y):
  cov = np.matrix([[1, 0.5], [0.5, 1]])
  scale = 0.5 if x < 0 else 4
  import scipy.integrate as integrate
  from venture.lite.utils import logDensityMVNormal
  def postprop(xout):
    prior = scipy.stats.norm.pdf(xout, loc=x, scale=scale)
    likelihood = logDensityMVNormal([0,0], np.array([xout,y]), cov)
    # TODO Should this be math.exp(likelihood)?
    return prior * likelihood
  (ans,_) = integrate.quad(postprop, x-4*scale, x+4*scale)
  return ans

def make_pic(name, inf_prog):
  model = HMCDemo(shortcuts.Lite().make_church_prime_ripl())
  history, _ = model.runFromConditional(
    70, runs=3, verbose=True, name=name, infer=inf_prog)
  return history


if __name__ == '__main__':
  # TODO To compare rejection sampling, would need to define
  # logDensityBound for MVNormalOutputPSP
  # make_pic("rej", "(rejection default all 1)")
  h1 = make_pic("hmc", "(hmc 'param all 0.1 20 1)")
  # h1.quickScatter("x", "y", style="-", contour_func=true_pdf, contour_delta=0.5)
  h2 = make_pic("mh", "(mh default one 10)")
  # h2.quickScatter("x", "y", style="-", contour_func=true_pdf, contour_delta=0.5)
  h3 = make_pic("map", "(map 'param all 0.1 2 1)")
  # h3.quickScatter("x", "y", style="-", contour_func=true_pdf, contour_delta=0.5)
  u.historyOverlay("demo", [("hmc", h1), ("mh", h2), ("map", h3)]) \
    .quickScatter("x", "y", contour_func=true_pdf, contour_delta=0.5)
