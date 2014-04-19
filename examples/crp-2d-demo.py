from venture import shortcuts
from venture.unit import VentureUnit, historyOverlay
from venture.sivm import VentureSivm
from venture import ripl
import scipy.io as sio
import numpy as np
import numpy.random as rd
import argparse
import sys
import time
from IPython.parallel import Client
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab

def toVentureArray(array, token='array'):
  return '(%s %s)'%(token, ' '.join(['%.20f'%(x) for x in array]))

def toVentureInternalArray(array, token='array'):
  return {"type":"list", "value":[{"type":"real", "value": x} for x in array]}

def toVentureMatrix(array):
  return '(matrix (list %s))'%(' '.join([toVentureArray(x, token='list') for x in array]))

class CRP2dMixtureDemo():
  def makeAssumes(self):
    self.ripl = shortcuts.make_lite_church_prime_ripl()
    self.ripl.assume('alpha', '(scope_include (quote hypers) 0 (gamma 1.0 1.0))')
    self.ripl.assume('scale', '(scope_include (quote hypers) 1 (gamma 1.0 1.0))')
    self.ripl.assume('crp', '(make_crp alpha)')
    self.ripl.assume('get_cluster', '''
      (mem (lambda (id)
            (scope_include (quote clustering) id (crp))))
      ''')
    self.ripl.assume('get_mean', '''
      (mem (lambda (cluster)
            (scope_include (quote parameters) cluster (multivariate_normal %s %s))))
      '''%(toVentureArray(np.zeros((1,2))[0]), toVentureMatrix(np.eye(2)*10)))
    # TODO: Add Inverse-Wishart Prior.
    self.ripl.assume('get_variance', '''
      (mem (lambda (cluster)
            (scope_include (quote parameters) cluster %s)))
      '''%toVentureMatrix(np.eye(2)))
    self.ripl.assume('get_component_model', '''
      (lambda (cluster)
            (lambda () (multivariate_normal (get_mean cluster) (get_variance cluster))))
      ''')
    self.ripl.assume('get_datapoint', '''
      (mem (lambda (id)
            ((get_component_model (get_cluster id)))))
      ''')



  def makeObserves(self):
    self.ripl.observe('(get_datapoint 0)', {'type': 'list', 'value': [{'type': 'real', 'value': -2.4121470179012272}, {'type': 'real', 'value': -4.0898807104175177}]})
    self.ripl.observe('(get_datapoint 1)', {'type': 'list', 'value': [{'type': 'real', 'value': -3.5742473969392483}, {'type': 'real', 'value': 16.047761595206289}]})
    self.ripl.observe('(get_datapoint 2)', {'type': 'list', 'value': [{'type': 'real', 'value': -0.44139814963230056}, {'type': 'real', 'value': -4.366209321011203}]})
    self.ripl.observe('(get_datapoint 3)', {'type': 'list', 'value': [{'type': 'real', 'value': -0.23258164982263235}, {'type': 'real', 'value': -5.687017265835844}]})
    self.ripl.observe('(get_datapoint 4)', {'type': 'list', 'value': [{'type': 'real', 'value': 0.035565573263568961}, {'type': 'real', 'value': -3.337136380872824}]})
    self.ripl.observe('(get_datapoint 5)', {'type': 'list', 'value': [{'type': 'real', 'value': -4.3443008510924654}, {'type': 'real', 'value': 17.827515632039944}]})
    self.ripl.observe('(get_datapoint 6)', {'type': 'list', 'value': [{'type': 'real', 'value': -0.19026889153157978}, {'type': 'real', 'value': -3.6065264508558972}]})
    self.ripl.observe('(get_datapoint 7)', {'type': 'list', 'value': [{'type': 'real', 'value': -4.8535236723040498}, {'type': 'real', 'value': 17.098870618931819}]})
    self.ripl.observe('(get_datapoint 8)', {'type': 'list', 'value': [{'type': 'real', 'value': -1.1235421108040797}, {'type': 'real', 'value': -5.261098458581845}]})
    self.ripl.observe('(get_datapoint 9)', {'type': 'list', 'value': [{'type': 'real', 'value': 1.1794444234381136}, {'type': 'real', 'value': -3.630199721409284}]})
    self.num_sample = 10

if __name__ == '__main__':
  model = CRP2dMixtureDemo()
  model.makeAssumes()
  model.makeObserves()
  def func(ripl, iter):
    ripl.infer("(cycle ((mh hypers one 2) (mh parameters one 3) (pgibbs clustering ordered 2 1)) 3)")
    # self.ripl.infer("(cycle ((mh hypers one 2) (mh parameters one 3) (mh clustering one 8)) 1)")
    # self.ripl.infer('(mh hypers one %d)'%iter)
    # self.ripl.infer('(mh clustering one %d)'%(iter))
    # self.ripl.infer('(mh parameters one %d)'%(iter))
    # self.ripl.infer('(hmc parameters all %f %d %d)'%(eps, L, iter))
    # self.ripl.infer('(pgibbs clustering ordered 2 %d)'%iter)
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
    return {'data':data_l, 'mean':mean_l, 'var':var_l, \
            'component_set':list(component_set)}
  mean_l = list()
  var_l = list()
  plt.ion()
  x_l = list()
  y_l = list()
  for ni in range(model.num_sample):
    dpoint = model.ripl.predict('(get_datapoint %d)'%ni)
    x_l.append(dpoint[0])
    y_l.append(dpoint[1])
  for ni in range(100):
    func(model.ripl, 1)
    plt.clf()
    sample = makeData(model.ripl, model.num_sample)
    mean_l.append(sample['mean'])
    var_l.append(sample['var'])
    print sample['mean']

    plt.plot(x_l, y_l, 'r.')
    for (mean_x,var_x) in zip(sample['mean'], sample['var']):
      plot_xrange = np.arange(2*min(x_l)-max(x_l), 2*max(x_l)-min(x_l), 2*(max(x_l)-min(x_l))/100)
      plot_yrange = np.arange(2*min(y_l)-max(y_l), 2*max(y_l)-min(y_l), 2*(max(y_l)-min(y_l))/100)
      plot_xrange, plot_yrange = np.meshgrid(plot_xrange, plot_yrange)
      plot_zrange = mlab.bivariate_normal(plot_xrange, plot_yrange, mean_x[0], mean_x[1],  \
                    var_x[0,0], var_x[1,1], var_x[0,1])

      plt.contour(plot_xrange, plot_yrange, plot_zrange)
    plt.draw()
    plt.show()

