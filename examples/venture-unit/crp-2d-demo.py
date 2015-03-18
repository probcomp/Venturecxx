import numpy as np
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab

from venture import shortcuts
import venture.value.dicts as v

def toVentureArray(array, token='array'):
  return '(%s %s)'%(token, ' '.join(['%.20f'%(x) for x in array]))

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
    self.ripl.observe('(get_datapoint 0)', v.list([v.real(-2.4121470179012272), v.real(-4.0898807104175177)]))
    self.ripl.observe('(get_datapoint 1)', v.list([v.real(-3.5742473969392483), v.real(16.047761595206289)]))
    self.ripl.observe('(get_datapoint 2)', v.list([v.num(-0.44139814963230056), v.num(-4.366209321011203)]))
    self.ripl.observe('(get_datapoint 3)', v.list([v.num(-0.23258164982263235), v.num(-5.687017265835844)]))
    self.ripl.observe('(get_datapoint 4)', v.list([v.num(0.035565573263568961), v.num(-3.337136380872824)]))
    self.ripl.observe('(get_datapoint 5)', v.list([v.num(-4.3443008510924654), v.num(17.827515632039944)]))
    self.ripl.observe('(get_datapoint 6)', v.list([v.num(-0.19026889153157978), v.num(-3.6065264508558972)]))
    self.ripl.observe('(get_datapoint 7)', v.list([v.num(-4.8535236723040498), v.num(17.098870618931819)]))
    self.ripl.observe('(get_datapoint 8)', v.list([v.num(-1.1235421108040797), v.num(-5.261098458581845)]))
    self.ripl.observe('(get_datapoint 9)', v.list([v.num(1.1794444234381136), v.num(-3.630199721409284)]))
    self.num_sample = 10

if __name__ == '__main__':
  model = CRP2dMixtureDemo()
  model.makeAssumes()
  model.makeObserves()
  def func(ripl, iter):
    ripl.infer("(repeat 3 (do (mh hypers one 2) (mh parameters one 3) (pgibbs clustering ordered 2 1)))")
    # self.ripl.infer("(repeat 1 (do (mh hypers one 2) (mh parameters one 3) (mh clustering one 8)))")
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

