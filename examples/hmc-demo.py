# Copyright (c) 2013, MIT Probabilistic Computing Project.
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
# You should have received a copy of the GNU General Public License along with Venture.  If not, see <http://www.gnu.org/licenses/>.

import scipy.stats
import numpy as np

from venture import shortcuts
import venture.unit as u

class HMCDemo(u.VentureUnit):
  def makeAssumes(self):
    program = """
[ASSUME x (scope_include (quote param) 0 (uniform_continuous -4 4))]
[ASSUME y (scope_include (quote param) 1 (uniform_continuous -4 4))]
[ASSUME xout (if (< x 0)
    (normal x 0.5)
    (normal x 4))]
[ASSUME out (multivariate_normal (array xout y) (matrix (list (list 1 0.5) (list 0.5 1))))]
"""
    commands = [command_str.split("]")[0].split(" ", 1) for command_str in program.strip().split("[ASSUME ") if command_str]
    for (var, exp) in commands:
      self.assume(var, exp)

  def makeObserves(self):
    pass

# int_R pdf(xout|x) pdf([0,0]|[xout, y])
def true_pdf(x, y):
  cov = np.matrix([[1, 0.5], [0.5, 1]])
  scale = 0.5 if x < 0 else 4
  import scipy.integrate as integrate
  from venture.lite.utils import logDensityMVNormal
  def postprop(xout):
    return scipy.stats.norm.pdf(xout, loc=x, scale=scale) * logDensityMVNormal([0,0], np.array([xout,y]), cov)
  (ans,_) = integrate.quad(postprop, x-4*scale, x+4*scale)
  return ans

def make_pic(name, inf_prog):
  def infer(ripl, _ct):
    observes_made = any(directive["instruction"] == "observe" for directive in ripl.list_directives())
    if not observes_made:
      # TODO This is a hack around there being no good way to observe
      # datastructures right now.
      v = [{"type": "real", "value": 0}, {"type": "real", "value": 0}]
      ripl.sivm.execute_instruction({"instruction":"observe","expression":"out","value":{"type":"list","value":v}})
      observes_made = True
    ripl.infer(inf_prog)
  model = HMCDemo(shortcuts.Lite().make_church_prime_ripl())
  history = model.runFromConditional(70, runs=3, verbose=True, name=name, infer=infer)
  return history

if __name__ == '__main__':
  # TODO To compare rejection sampling, would need to define logDensityBound for MVNormalOutputPSP
  # make_pic("rej", "(rejection default all 1)")
  h1 = make_pic("hmc", "(hmc param all 0.1 20 1)")
  # h1.quickScatter("x", "y", style="-")
  h2 = make_pic("mh", "(mh default one 10)")
  u.historyOverlay("demo", [("hmc", h1), ("mh", h2)]).quickScatter("x", "y", contour_func=true_pdf)
  # TODO Plotting the contours would require integrating out the intermediate normal, which I do not wish to do now.
  # plot_contours(xs, ys, lambda x, y: scipy.stats.norm.pdf(x, loc=0, scale=3) * scipy.stats.norm.pdf(y, loc=0, scale=2))
