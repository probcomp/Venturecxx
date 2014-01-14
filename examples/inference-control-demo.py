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
[ASSUME alpha (scope_include hypers default (uniform_continuous 0 10))]
[ASSUME scale (scope_include hypers default (uniform_continuous 0 10))]

[ASSUME pyp_make (lambda (alpha) (lambda () 1))]

[ASSUME pyp (pyp_make alpha)]

[ASSUME get_cluster (mem (lambda (id)
  (scope_include clustering default (pyp))))]

[ASSUME get_mean (mem (lambda (cluster)
  (scope_include parameters cluster
    (normal 0 10))))]

[ASSUME get_variance (mem (lambda (cluster)
  (scope_include parameters cluster
    (gamma 1 scale))))]

[ASSUME get_component_model (lambda (cluster)
  (lambda () (normal (get_mean cluster) (get_variance cluster))))]

[ASSUME get_datapoint (mem (lambda (id)
  ((get_component_model (get_cluster id)))))]
"""
    commands = [command_str.split("]")[0].split(" ", 1) for command_str in program.strip().split("[ASSUME ") if command_str]
    for (var, exp) in commands:
      self.assume(var, exp)

  def makeObserves(self):
    self.observe("(get_datapoint 1)", 0)
    self.observe("(get_datapoint 2)", -5)
    self.observe("(get_datapoint 3)", 5)

if __name__ == '__main__':
  ripl = shortcuts.make_lite_church_prime_ripl()
  model = PitmanYorMixtureDemo(ripl)
  def blockInfer(ripl, ct): # Is this the same thing as "church default" from the email?
    ripl.infer({"transitions":ct, "kernel":"mh", "scope":"default", "block":"all"})
  def statisticsInfer(ripl, ct):
    # Note: this is equivalent to "block":"all" because the "hypers"
    # scope has only one block.
    hypers =     {"kernel":"mh", "scope":"hypers", "block":"one", "transitions":10}
    # Ditto, but for a stupid reason (blocks are not expressions right now)
    parameters = {"kernel":"mh", "scope":"parameters", "block":"one", "transitions":50}
    # Ditto, for the same stupid reason (blocks are not expressions right now)
    clustering = {"kernel":"mh", "scope":"clustering", "block":"one", "transitions":50}
    ripl.infer({"transitions":10, "kernel":"cycle", "subkernels":[hypers, parameters, clustering]})
  for (name,inference) in [("defaultMH", None), ("blockMH", blockInfer),
                           ("statisticsDefault", statisticsInfer)]:
    # history = model.runFromConditional(5, runs=2, verbose=True, name=name, infer=inference)
    # history.plot(fmt='png')
    (sampled, inferred, kl) = model.computeJointKL(5, 30, runs=3, verbose=True, name=name, infer=inference)
    sampled.plot(fmt='png')
    inferred.plot(fmt='png')
    kl.plot(fmt='png')
