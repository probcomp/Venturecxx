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

def hmcInfer(ripl, _ct):
  ripl.infer("(hmc default all 2)")

def main():
  model = HMCDemo(shortcuts.Lite().make_church_prime_ripl())
  history = model.runFromConditional(20, runs=1, verbose=True, name="hmc", infer=hmcInfer)
  xs = history.nameToSeries["x"][0].values
  ys = history.nameToSeries["y"][0].values
  plt.figure()
  plt.clf()
  plt.title("HMC trajectory")
  plt.xlabel("x")
  plt.ylabel("y")
  plt.plot(xs, ys, '.', label="hmc")
  u.legend_outside()
  u.savefig_legend_outside("demo.png")

if __name__ == '__main__':
  main()
