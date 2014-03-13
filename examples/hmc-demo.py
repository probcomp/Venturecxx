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
[ASSUME x (normal 0 3)]
[ASSUME y (normal 0 2)]
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

def make_pic(name, inf_prog):
  def infer(ripl, _ct):
    ripl.infer(inf_prog)
  model = HMCDemo(shortcuts.Lite().make_church_prime_ripl())
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
  make_pic("hmc", "(hmc default all 1)")
  make_pic("mh", "(mh default all 1)")
