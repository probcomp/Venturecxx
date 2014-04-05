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
from venture.unit import VentureUnit, historyOverlay

class Sprinkler(VentureUnit):
  def makeAssumes(self):
    self.assume("rain","(bernoulli 0.2)")
    self.assume("sprinkler","(bernoulli (if rain 0.01 0.4))")
    self.assume("grassWet","""
(bernoulli
 (if rain
   (if sprinkler 0.99 0.8)
   (if sprinkler 0.9 0.00001)))
""")

  def makeObserves(self):
    self.observe("grassWet", True)

if __name__ == '__main__':
  ripl = shortcuts.make_lite_church_prime_ripl()
  model = Sprinkler(ripl)
  history1 = model.runFromConditional(20, verbose=True, name="defaultMH")
#  history1.plot(fmt='png')
  history1.plotOneSeries("sprinkler", fmt='png', ybounds=[-20,30])

  # def blockInfer(ripl, ct):
  #       ripl.infer({"transitions":ct, "kernel":"mh", "scope":"default", "block":"all")
  # history = model.runFromConditional(50, verbose=True, infer=blockInfer, name="blockMH")
  # history.plot(fmt='png')

  model = Sprinkler(shortcuts.make_puma_church_prime_ripl())
  history2 = model.runFromConditional(20, verbose=True, name="defaultMH-Puma")
  history2.plot(fmt='png')

  history3 = historyOverlay("sprinkler", [("Lite", history1), ("Puma", history2)])
  history3.plot(fmt='png')
