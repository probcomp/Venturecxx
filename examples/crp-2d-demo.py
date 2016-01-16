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

"""2-D Chinese Restaurant Clustering example.

The clusters are 2-D Gaussian.  The model infers the number of
clusters using a Chinese Restaurant Process prior on the partition of
the data into clusters.

TODO: May not actually work properly (cluster means don't seem to move?)
"""

import math

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab

from venture import shortcuts
import venture.value.dicts as v

model = '''
[assume alpha (tag (quote hypers) 0 (gamma 1.0 1.0))]
[assume scale (tag (quote hypers) 1 (gamma 1.0 1.0))]
[assume crp (make_crp alpha)]
[assume get_cluster
  (mem (lambda (id)
    (tag (quote clustering) id (crp))))]
[assume mean_hyper_mean (array 0 0)]
[assume mean_hyper_variance (matrix (list (list 10 0) (list 0 10)))]
[assume get_mean
  (mem (lambda (cluster)
    (tag (quote parameters) cluster
      (multivariate_normal mean_hyper_mean mean_hyper_variance))))]
;; TODO: Add Inverse-Wishart Prior.
[assume variance (matrix (list (list 1 0) (list 0 1)))]
[assume get_variance
  (mem (lambda (cluster)
    (tag (quote parameters) cluster variance)))]
[assume get_component_model
  (lambda (cluster)
    (lambda ()
      (multivariate_normal (get_mean cluster) (get_variance cluster))))]
[assume get_datapoint
  (mem (lambda (id)
    ((get_component_model (get_cluster id)))))]
'''


def makeObserves(ripl):
  ripl.observe('(get_datapoint 0)', v.list([v.real(-2.4121470179012272), v.real(-4.0898807104175177)]))
  ripl.observe('(get_datapoint 1)', v.list([v.real(-3.5742473969392483), v.real(16.047761595206289)]))
  ripl.observe('(get_datapoint 2)', v.list([v.num(-0.44139814963230056), v.num(-4.366209321011203)]))
  ripl.observe('(get_datapoint 3)', v.list([v.num(-0.23258164982263235), v.num(-5.687017265835844)]))
  ripl.observe('(get_datapoint 4)', v.list([v.num(0.035565573263568961), v.num(-3.337136380872824)]))
  ripl.observe('(get_datapoint 5)', v.list([v.num(-4.3443008510924654), v.num(17.827515632039944)]))
  ripl.observe('(get_datapoint 6)', v.list([v.num(-0.19026889153157978), v.num(-3.6065264508558972)]))
  ripl.observe('(get_datapoint 7)', v.list([v.num(-4.8535236723040498), v.num(17.098870618931819)]))
  ripl.observe('(get_datapoint 8)', v.list([v.num(-1.1235421108040797), v.num(-5.261098458581845)]))
  ripl.observe('(get_datapoint 9)', v.list([v.num(1.1794444234381136), v.num(-3.630199721409284)]))

def doit():
  num_sample = 10
  ripl = shortcuts.make_lite_church_prime_ripl()
  ripl.execute_program(model)
  makeObserves(ripl)
  def func(ripl, iter):
    ripl.infer("(repeat 3 (do (mh 'hypers one 2) (mh 'parameters one 3) (pgibbs 'clustering ordered 2 1)))")
    # self.ripl.infer("(repeat 1 (do (mh 'hypers one 2) (mh 'parameters one 3) (mh 'clustering one 8)))")
    # self.ripl.infer('(mh 'hypers one %d)'%iter)
    # self.ripl.infer('(mh 'clustering one %d)'%(iter))
    # self.ripl.infer('(mh 'parameters one %d)'%(iter))
    # self.ripl.infer('(hmc 'parameters all %f %d %d)'%(eps, L, iter))
    # self.ripl.infer('(pgibbs 'clustering ordered 2 %d)'%iter)
  def makeData(ripl, num_sample):
    data_l = list()
    mean_l = list()
    var_l = list()
    component_set = set()
    for ni in range(num_sample):
      data_l.append(ripl.predict('(get_datapoint %d)'%ni))
      # print 'ni = %d, cluster = %d'%(ni, self.ripl.predict('(get_cluster %d)'%ni))
      component_set.add(ripl.predict('(get_cluster %d)'%ni))
      # print data_l[-1]
    for ci in component_set:
      mean_l.append(ripl.predict('(get_mean %d)'%ci))
      var_l.append(ripl.predict('(get_variance %d)'%ci))
    # print 'components: ', component_set
    # print 'mean: ', mean_l
    # print 'variance: ', var_l
    return {'data':data_l, 'mean':mean_l, 'var':var_l, \
            'component_set':list(component_set)}
  plt.ion()
  x_l = list()
  y_l = list()
  for ni in range(num_sample):
    dpoint = ripl.predict('(get_datapoint %d)'%ni)
    x_l.append(dpoint[0])
    y_l.append(dpoint[1])
  for ni in range(100):
    func(ripl, 1)
    plt.clf()
    sample = makeData(ripl, num_sample)
    print sample['mean']

    plt.plot(x_l, y_l, 'r.')
    for (mean_x,var_x) in zip(sample['mean'], sample['var']):
      plot_xrange = np.arange(2*min(x_l)-max(x_l), 2*max(x_l)-min(x_l), 2*(max(x_l)-min(x_l))/100)
      plot_yrange = np.arange(2*min(y_l)-max(y_l), 2*max(y_l)-min(y_l), 2*(max(y_l)-min(y_l))/100)
      plot_xrange, plot_yrange = np.meshgrid(plot_xrange, plot_yrange)
      plot_zrange = mlab.bivariate_normal(plot_xrange, plot_yrange, \
          mux=mean_x[0], muy=mean_x[1],  \
          sigmax=math.sqrt(var_x[0,0]), sigmay=math.sqrt(var_x[1,1]), \
          sigmaxy=math.sqrt(var_x[0,1]))

      plt.contour(plot_xrange, plot_yrange, plot_zrange)
    plt.draw()
    plt.show()

if __name__ == '__main__':
  doit()
