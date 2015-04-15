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
import matplotlib
matplotlib.use('Agg')

from venture import shortcuts
from venture.unit import VentureUnit, productMap, plotAsymptotics

class HMMDemo(VentureUnit):
  def makeAssumes(self):
    program = """
[ASSUME observation_noise (tag (quote hypers) 0 (gamma 1.0 1.0))]

[ASSUME get_state
  (mem (lambda (t)
	 (if (= t 0) 
	     (tag (quote state) 0 (bernoulli 0.3))
	     (transition_fn (get_state (- t 1)) t))))]

[ASSUME get_observation
  (mem (lambda (t)
	 (observation_fn (get_state t))))]

[ASSUME transition_fn
  (lambda (state t)
    (if state
        (tag (quote state) t (bernoulli 0.7))
        (tag (quote state) t (bernoulli 0.3))))]

[ASSUME observation_fn
  (lambda (state)
    (normal (if state 3 -3) observation_noise))]

"""
    commands = [command_str.split("]")[0].split(" ", 1) for command_str in program.strip().split("[ASSUME ") if command_str]
    for (var, exp) in commands:
      self.assume(var.strip(), exp)

  def makeObserves(self):
    xs = [4.17811131241034, 3.8207451562269097, 3.8695630629179485,
          0.22006118284977338, 2.210199033799397, 3.783908156611711,
          2.837419867371207, 1.317835790137246, -0.16712980626716778,
          2.9172052420088024, 2.510820987230155, 3.8160095647125587,
          2.1845237960891737, 4.857767012696541, 3.575666111020788,
          0.5826540416187078, 4.911935337633685, 1.6865857289172699,
          2.096957795256201, 3.962559707705782, 2.0649737290837695,
          4.447773338208195, 3.0441473773992254, 1.9403530443371844,
          2.149892339815339, 1.8535027835799924, 1.3764327100611682,
          2.787737100652772, 4.605218953213757, 4.3600668534442955,
          4.479476152575004, 2.903384365135718, 3.228308841685054,
          2.768731834655059, 2.677169426912596, 4.548729323863021,
          4.45470931661095, 2.2756630109749754, 3.8043219817661464,
          4.041893001861111, 4.932539777501281, 3.392272043248744,
          3.5285486875160186, 1.7961542635140841, 2.9493126820691664,
          1.7582718429078779, 3.444330463983401, 2.031284816908312,
          1.6347773147087383, 4.423285189276542, 0.5149704854992727,
          4.470589149104097, 4.4519204418264575, 3.610788527431577,
          3.7908243330830036, 3.0038367596454187, 3.3486671878130028,
          4.474091346599369, 2.7734106792197633, 1.8127987198750086]

    xs[3:7] = [-x for x in xs[5:10]]
    xs[17:23] = [-x for x in xs[17:23]]
    if "length" in self.parameters:
      num_obs = min(len(xs), int(self.parameters["length"]))
    else:
      num_obs = 6
    for i in range(num_obs):
      self.observe("(observation_fn (get_state %d))" % i, xs[i])

def commandInfer(command):
  def infer(ripl, _): ripl.infer(command)
  return infer

def runner(params):
  print "Running with params %s" % params
  model = HMMDemo(shortcuts.make_lite_church_prime_ripl(), params)
  return model.runFromConditional(3, runs=3, verbose=True, infer=commandInfer(params["command"]))

def main2():
  parameters = {"length": [5,10,15,20,25,30,35,40,45,50,55],
                "command": ["(repeat 1 (do (mh hypers one 3) (pgibbs state ordered 4 1)))",
                            "(repeat 1 (do (mh hypers one 3) (func_pgibbs state ordered 4 1)))"]}
  histories = productMap(parameters, runner)
  plotAsymptotics(parameters, histories, 'sweep time (s)', fmt='png', aggregate=True)
  plotAsymptotics(parameters, histories, 'sweep time (s)', fmt='png')

if __name__ == '__main__':
  main2()
