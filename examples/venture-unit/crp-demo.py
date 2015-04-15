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
from venture.unit import VentureUnit

class CRPMixtureDemo(VentureUnit):
  def makeAssumes(self):
    program = """
[ASSUME alpha (tag (quote hypers) 0 (gamma 1.0 1.0))]
[ASSUME scale (tag (quote hypers) 1 (gamma 1.0 1.0))]

[ASSUME crp (make_crp alpha)]

[ASSUME get_cluster (mem (lambda (id)
  (tag (quote clustering) id (crp))))]

[ASSUME get_mean (mem (lambda (cluster)
  (tag (quote parameters) cluster (normal 0 10))))]

[ASSUME get_variance (mem (lambda (cluster)
  (tag (quote parameters) cluster (gamma 1 scale))))]

[ASSUME get_component_model (lambda (cluster)
  (lambda () (normal (get_mean cluster) (get_variance cluster))))]

[ASSUME get_datapoint (mem (lambda (id)
  ((get_component_model (get_cluster id)))))]
"""
    commands = [command_str.split("]")[0].split(" ", 1) for command_str in program.strip().split("[ASSUME ") if command_str]
    for (var, exp) in commands:
      self.assume(var, exp)

  def makeObserves(self):
    # c1 = N(10,2)
    c1 = [8.438862313274857,5.986118444655459,12.247737612651065,9.98003406064534,6.767930993829122,7.344284453098805,12.294722601146331,9.701152326601933,9.196654198557628,9.721257753586972,11.879811886237212,12.753438617110762,9.249177005620366,9.180626862859654,9.968920688596375,11.068365699395546,8.467135099381293,11.593115183867898,12.87103678320512,12.42059711947659]

    # c2 = N(-10,3)
    c2 = [-7.99213651575986, -11.096979657618158, -17.052502285654725, -7.84272275196337, -14.289500064400832, -10.633792565831728, -14.957711186216947, -6.231328859617913, -13.364682023393655, -12.945119714485587, -6.722133626479774, -8.566409958446435, -6.413996337359148, -11.624816531768026, -7.785228361837747, -12.276244769701753, -14.503007395573675, -9.76446095528871, -8.228219351639927, -9.741998170761416]

    # c3 = N(0,1.5)
    c3 = [1.2862190097549782, -2.0918456617214947, -2.466858195215555, -0.9989735378944502, 1.6654310434851636, -0.47667095805497206, 1.2842732995675072, -1.4688099699500534, 0.5895325341217226, 0.2894536369600946, 0.4618849196904734, 0.4678957436449437, -2.077507965906229, -2.566577198660523, 0.8964088468588131, -0.9752402407709437, 3.084206058143385, -1.5056921323213415, -1.6942644719468085, 2.307315802945018]

    for i in range(len(c1)):
#    for i in range(2):
      self.observe("(get_datapoint %d)" % i, c1[i])
      self.observe("(get_datapoint %d)" % (len(c1) + i), c2[i])
      self.observe("(get_datapoint %d)" % (len(c1) + len(c2) + i), c3[i])

def run(arg):
  name = arg[0]
  inference = arg[1]

  # history = model.runFromConditional(100, runs=10, verbose=True, name=name, infer=inference)[0]
  history = model.runFromConditional(5, runs=3, verbose=True, name=name, infer=inference)[0]
  history.plot(fmt='png')
  # (sampled, inferred, kl) = model.computeJointKL(5, 200, runs=3, verbose=True, name=name, infer=inference)
  # (sampled, inferred, kl) = model.computeJointKL(3, 20, runs=1, verbose=True, name=name, infer=inference)
  # sampled.plot(fmt='png')
  # inferred.plot(fmt='png')
  # kl.plot(fmt='png')

if __name__ == '__main__':
  model = CRPMixtureDemo(shortcuts.make_lite_church_prime_ripl())
  def statisticsInfer(ripl, _):
    # ripl.infer("(repeat 10 (do (mh hypers one 5) (mh parameters one 20) (mh clustering one 80)))")
    ripl.infer("(repeat 1 (do (mh hypers one 2) (mh parameters one 3) (mh clustering one 8)))")
  def pGibbsInfer(ripl, _):
    # ripl.infer("(repeat 10 (do (mh hypers one 5) (mh parameters one 20) (pgibbs clustering ordered 2 1)))")
    ripl.infer("(repeat 3 (do (mh hypers one 2) (mh parameters one 3) (pgibbs clustering ordered 2 1)))")
  multiprocess = False
  if multiprocess:
    from multiprocessing import Pool
    pool = Pool(30)
    pool.map(run, [("crp_defaultMH", None),
                   ("crp_statisticsInfer", statisticsInfer),
                   ("crp_pGibbsInfer",pGibbsInfer)])
  else:
    map(run, [("crp_defaultMH", None),
              ("crp_statisticsInfer", statisticsInfer),
              ("crp_pGibbsInfer",pGibbsInfer)])
