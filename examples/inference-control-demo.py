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
from venture import shortcuts
from venture.unit import *

class PitmanYorMixtureDemo(VentureUnit):
  def makeAssumes(self):
    program = """
[ASSUME alpha (scope_include hypers default (uniform 0 10))]
[ASSUME scale (scope_include hypers default (uniform 0 10))]

[ASSUME pyp (pyp/make alpha)]

[ASSUME get_cluster (mem (lambda (id) (scope_include clustering default (pyp)) ))]

[ASSUME get_mean (mem (lambda (cluster)
  (scope_include parameters cluster
     (normal 0 10) ))]

[ASSUME get_variance (mem (lambda (cluster)
  (scope_include parameters cluster
     (gamma 1 scale) ))]

[ASSUME get_component_model (mem (lambda (cluster)
  (normal (get_mean cluster) (get_variance cluster)) ))]

[ASSUME get_datapoint (mem (lambda (id) ( (get_component_model (get_cluster id)) ) ))]
"""
    commands = [command_str.split("]")[0].split(" ", 1) for command_str in program.strip().split("[ASSUME ") if command_str]
    for (var, exp) in commands:
      self.assume(var, exp)

  def makeObserves(self):
    self.observe("(get_datapoint 1)", 0)
    self.observe("(get_datapoint 2)", -5)
    self.observe("(get_datapoint 3)", 5)

if __name__ == '__main__':
  ripl = shortcuts.make_church_prime_ripl()
  model = PitmanYorMixtureDemo(ripl)
  history = model.runFromConditional(5, runs=2, verbose=True, name="defaultMH")
  history.plot(fmt='png')
  def blockInfer(ripl, ct):
    ripl.infer(ct, block="all")
  history = model.runFromConditional(5, runs=2, verbose=True, infer=blockInfer, name="blockMH")
  history.plot(fmt='png')
