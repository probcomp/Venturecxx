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
"""

import math

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab

from venture import shortcuts
import venture.value.dicts as v

model = '''
[assume alpha (tag (quote hypers) 0 (gamma 1.0 1.0))]
[assume crp (make_crp alpha)]
[assume get_cluster
  (mem (lambda (id)
    (tag (quote clustering) id (crp))))]
[assume mean_hyper_mean (array 0 0)]
[assume mean_hyper_variance (matrix (list (list 20 0) (list 0 20)))]
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


def makeObserves(ripl, num_points):
  data = [v.list([v.real(-2.4121470179012272), v.real(-4.0898807104175177)]),
          v.list([v.real(-3.5742473969392483), v.real(16.047761595206289)]),
          v.list([v.num(-0.44139814963230056), v.num(-4.366209321011203)]),
          v.list([v.num(-0.23258164982263235), v.num(-5.687017265835844)]),
          v.list([v.num(0.035565573263568961), v.num(-3.337136380872824)]),
          v.list([v.num(-4.3443008510924654), v.num(17.827515632039944)]),
          v.list([v.num(-0.19026889153157978), v.num(-3.6065264508558972)]),
          v.list([v.num(-4.8535236723040498), v.num(17.098870618931819)]),
          v.list([v.num(-1.1235421108040797), v.num(-5.261098458581845)]),
          v.list([v.num(1.1794444234381136), v.num(-3.630199721409284)])]
  for i in range(num_points):
    ripl.observe('(get_datapoint %d)' % i, data[i])

def do_infer(ripl, iter):
  ripl.infer("(mh default one 50)")
  # ripl.infer("""(repeat 3 (do
  #   (mh 'hypers one 2)
  #   (mh 'parameters one 3)
  #   (pgibbs 'clustering ordered 2 1)))""")
  # self.ripl.infer("(repeat 1 (do (mh 'hypers one 2) (mh 'parameters one 3) (mh 'clustering one 8)))")
  # self.ripl.infer('(mh 'hypers one %d)'%iter)
  # self.ripl.infer('(mh 'clustering one %d)'%(iter))
  # self.ripl.infer('(mh 'parameters one %d)'%(iter))
  # self.ripl.infer('(hmc 'parameters all %f %d %d)'%(eps, L, iter))
  # self.ripl.infer('(pgibbs 'clustering ordered 2 %d)'%iter)

def collect_clusters(ripl, num_points):
  mean_l = list()
  var_l = list()
  component_set = set()
  for ni in range(num_points):
    # print 'ni = %d, cluster = %d'%(ni, self.ripl.predict('(get_cluster %d)'%ni))
    component_set.add(ripl.sample('(get_cluster %d)'%ni))
  for ci in component_set:
    mean_l.append(ripl.sample('(get_mean atom<%d>)'%ci))
    var_l.append(ripl.sample('(get_variance atom<%d>)'%ci))
  # print 'components: ', component_set
  # print 'mean: ', mean_l
  # print 'variance: ', var_l
  return {'mean':mean_l, 'var':var_l, \
          'component_set':list(component_set)}

def do_plot(x_l, y_l, sample, show_pics):
  plt.clf()
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
  if show_pics:
    plt.draw()
    plt.show()

def doit(num_points, num_frames, show_pics):
  ripl = shortcuts.make_lite_church_prime_ripl()
  ripl.execute_program(model)
  makeObserves(ripl, num_points)
  if show_pics:
    plt.ion()
  x_l = list()
  y_l = list()
  for ni in range(num_points):
    dpoint = ripl.sample('(get_datapoint %d)'%ni)
    x_l.append(dpoint[0])
    y_l.append(dpoint[1])
  for ni in range(num_frames):
    do_infer(ripl, 1)
    clusters = collect_clusters(ripl, num_points)
    if show_pics:
      print "Cluster means:", clusters['mean']
    do_plot(x_l, y_l, clusters, show_pics=show_pics)

if __name__ == '__main__':
  doit(num_points=10, num_frames=100, show_pics=True)
