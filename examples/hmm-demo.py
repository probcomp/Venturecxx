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

from venture import shortcuts
from venture.unit import VentureUnit


class HMMDemo(VentureUnit):
  def makeAssumes(self):
    program = """
[ASSUME observation_noise (scope_include (quote hypers) (quote unique) (gamma 1.0 1.0))]

[ASSUME get_state
  (mem (lambda (t)
	 (if (= t 0) 
	     (scope_include (quote state) 0 (bernoulli 0.3))
	     (transition_fn (get_state (- t 1)) t))))]

[ASSUME get_observation
  (mem (lambda (t)
	 (observation_fn (get_state t))))]

[ASSUME transition_fn
  (lambda (state t)
    (if state
        (scope_include (quote state) t (bernoulli 0.7))
        (scope_include (quote state) t (bernoulli 0.3))))]

[ASSUME observation_fn
  (lambda (state)
    (normal (if state 3 -3) observation_noise))]

"""
    commands = [command_str.split("]")[0].split(" ", 1) for command_str in program.strip().split("[ASSUME ") if command_str]
    for (var, exp) in commands:
      self.assume(var, exp)

  def makeObserves(self):
    xs = [4.17811131241034, 3.8207451562269097, 3.8695630629179485, 0.22006118284977338, 2.210199033799397, 3.783908156611711, 2.837419867371207, 1.317835790137246, -0.16712980626716778, 2.9172052420088024, 2.510820987230155, 3.8160095647125587, 2.1845237960891737, 4.857767012696541, 3.575666111020788, 0.5826540416187078, 4.911935337633685, 1.6865857289172699, 2.096957795256201, 3.962559707705782, 2.0649737290837695, 4.447773338208195, 3.0441473773992254, 1.9403530443371844, 2.149892339815339, 1.8535027835799924, 1.3764327100611682, 2.787737100652772, 4.605218953213757, 4.3600668534442955]

    xs[3:7] = [-x for x in xs[5:10]]
    xs[17:23] = [-x for x in xs[17:23]]
#    for i in range(len(xs)):
    for i in range(6):
      self.observe("(observation_fn (get_state %d))" % i, xs[i])

if __name__ == '__main__':
  model = HMMDemo(shortcuts.make_lite_church_prime_ripl())
  def particleFilterInfer(ripl, ct):
    ripl.infer({"transitions":2, "kernel":"pgibbs", "scope":"state", "block":"ordered", "particles":2})

  # def blockMH(ripl, ct):
  #   # TODO does this sort the default blocks in any reasonable way?
  #   ripl.infer({"transitions":10, "kernel":"pgibbs", "scope":"default", "block":"all", "particles":2})

  def reasonableInferMutative(ripl, ct):
    # hypers = {"kernel":"mh", "scope":"hypers", "block":"one", "transitions":10}
    # state = {"kernel":"pgibbs", "scope":"state", "block":"ordered", "transitions":1, "particles":2}
    # ripl.infer({"transitions":10, "kernel":"cycle", "subkernels":[hypers, state]})

    hypers = {"kernel":"mh", "scope":"hypers", "block":"one", "transitions":3}
    state = {"kernel":"pgibbs", "scope":"state", "block":"ordered", "transitions":1, "particles":4, "with_mutation":True}
    ripl.infer({"transitions":1, "kernel":"cycle", "subkernels":[hypers, state]})

  def reasonableInferPersistent(ripl, ct):
    hypers = {"kernel":"mh", "scope":"hypers", "block":"one", "transitions":3}
    state = {"kernel":"pgibbs", "scope":"state", "block":"ordered", "transitions":1, "particles":4, "with_mutation":False}
    ripl.infer({"transitions":1, "kernel":"cycle", "subkernels":[hypers, state]})

  def run(arg):
    name = arg[0]
    inference = arg[1]

    history = model.runFromConditional(2, runs=1, verbose=True, name=name, infer=inference)
    history.plot(fmt='png')

  work = [#("hmm_defaultMH", None),
          # ("hmm_particleFilterInfer",particleFilterInfer),
          #("hmm_reasonableInferMutative",reasonableInferMutative),
          ("hmm_reasonableInferPersistent",reasonableInferPersistent)]

  from multiprocessing import Pool
#  pool = Pool(3)
#  pool.map(run, work)
  # Running the job in-process gives better exceptions
  map(run, work)

  #    history = model.runFromConditional(5, runs=5, verbose=True, name=name, infer=inference)
  #    history.plot(fmt='png')
      # (sampled, inferred, kl) = model.computeJointKL(1, 20, runs=1, verbose=True, name=name, infer=inference)
      # sampled.plot(fmt='png')
      # inferred.plot(fmt='png')
      # kl.plot(fmt='png')
