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
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import scipy.stats
import numpy as np

from venture import shortcuts
import venture.unit as u

class HMCDemo(u.VentureUnit):
  def makeAssumes(self):
    program = """
[ASSUME x (uniform_continuous -10 10)]
[ASSUME y (uniform_continuous -10 10)]
[ASSUME xout (if (< x 0)
    (normal x 1)
    (normal x 2))]
[ASSUME out (multivariate_normal (array xout y) (matrix (list (list 1 3) (list 3 1))))]
"""
    commands = [command_str.split("]")[0].split(" ", 1) for command_str in program.strip().split("[ASSUME ") if command_str]
    for (var, exp) in commands:
      self.assume(var, exp)

  def makeObserves(self):
    pass

def plot_contours(xs, ys, func):
  xmin = min(xs)
  xmax = max(xs)
  ymin = min(ys)
  ymax = max(ys)
  delta = 0.25
  x = np.arange(xmin, xmax, delta)
  y = np.arange(ymin, ymax, delta)
  X, Y = np.meshgrid(x, y)
  Z = np.vectorize(func)(X,Y)
  plt.contour(X, Y, Z)

observes_made = False

def make_pic(name, inf_prog):
  global observes_made
  def infer(ripl, _ct):
    global observes_made
    print observes_made
    if not observes_made:
      # TODO This is a hack around there being no good way to observe
      # datastructures right now.
      v = [{"type": "real", "value": 0}, {"type": "real", "value": 0}]
      ripl.sivm.execute_instruction({"instruction":"observe","expression":"out","value":{"type":"list","value":v}})
      observes_made = True
    print observes_made
    print ripl.list_directives()
    ripl.infer(inf_prog)
  model = HMCDemo(shortcuts.Lite().make_church_prime_ripl())
  observes_made = False
  history = model.runFromConditional(200, runs=1, verbose=True, name=name, infer=infer)
  xs = history.nameToSeries["x"][0].values
  ys = history.nameToSeries["y"][0].values
  plt.figure()
  plt.clf()
  plt.title("%s trajectory" % name)
  plt.xlabel("x")
  plt.ylabel("y")
  plt.plot(xs, ys, '.', label=inf_prog)
  # for (i, (x, y)) in enumerate(zip(xs, ys)):
  #   plt.text(x, y, i)
  plot_contours(xs, ys, lambda x, y: scipy.stats.norm.pdf(x, loc=0, scale=3) * scipy.stats.norm.pdf(y, loc=0, scale=2))
  u.legend_outside()
  u.savefig_legend_outside("%s-demo.png" % name)

if __name__ == '__main__':
  make_pic("hmc", "(hmc default all 0.05 20 1)")
  make_pic("mh", "(mh default all 1)")
