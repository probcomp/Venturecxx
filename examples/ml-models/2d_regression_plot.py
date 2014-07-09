'''
Illustrates sequential Bayesian updating in Venture, for linear regression
model in 2 dimensions
'''

from __future__ import division
import re
from venture.shortcuts import (make_puma_church_prime_ripl,
                               make_lite_church_prime_ripl)
import numpy as np, scipy as sp, pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns
from os import path
import os
import cPickle as pkl
import sys
import time
import matplotlib as mpl

def make_data():
  w = matrix([0.5, -0.25]).T
  sigma_2 = 1
  X = matrix(np.random.uniform(-1, 1, size = [20,2]))
  y = matrix(np.random.normal(X * w, np.sqrt(sigma_2)))
  return {'X' : X, 'y' : y, 'w' : w, 'sigma_2' : sigma_2}

def load_model(infile):
  with open(infile) as f:
    lines = [x.strip() for x in f.readlines()]
  pass_next = False
  res = []
  for counter, line in enumerate(lines):
    pass_this = pass_next
    pass_next = False
    if pass_this:
      continue
    if re.match('^;', line) or not line:
      continue
    if 'assume D' in line:
      D = int(line.split(' ')[2][:-1])
    if line == '...':
      pass_next = True
      # get the previous line, and loop
      nextline = lines[counter+1]
      fmt_string = nextline.replace('D', '{i}')
      for i in range(2, D + 1):
        res.append(fmt_string.format(i = i))
    elif '...' in line:
      symbol = line.split()[1]
      replacement = ' '.join([symbol + '_' + str(i) for i in range(2, D + 1)])
      newline = line.replace('...', replacement).replace(' ' + symbol + '_D', '')
      res.append(newline)
    else:
      res.append(line)
  res = '\n'.join(res)
  return res

def build_ripl(infile = 'regression1.vnt'):
  model = load_model(infile)
  r = make_lite_church_prime_ripl()
  r.load_prelude()
  _ = r.execute_program(model)
  return r

def simulate_linear(infile = 'regression1.vnt'):
  r = build_ripl(infile)
  _ = r.forget('sigma_2')
  _ = r.assume('sigma_2', 1, label = 'sigma_2')
  _ = r.forget('w')
  _ = r.assume('w', '(vector 3 -2)', label = 'w')
  _ = r.assume('mem_unif', '(mem (lambda (i) (uniform_continuous -1 1)))')
  _ = r.assume('simulate', '(lambda (i) (list (mem_unif i) (y (vector 1 (mem_unif i)))))')
  res = {'x' : [], 'y' : []}
  for i in range(30):
    thisone = r.sample('(simulate {0})'.format(i))
    res['x'].append(thisone[0])
    res['y'].append(thisone[1])
  return pd.DataFrame(res)

def simulate_save(infile = 'regression1.vnt'):
  '''
  Save the data so I can run the inference on 4 different machines
  '''
  ds = simulate_linear(infile)
  outdir = path.join(path.dirname(path.realpath(__file__)), 'regression-evolution')
  out = path.join(outdir, 'data.txt')
  ds.to_csv(out, sep = '\t', index = False, float_format = '%0.4f')

# simulate_save()

def runme(name, method):
  res = []
  outdir = path.join(path.dirname(path.realpath(__file__)), 'regression-evolution')
  datafile = path.join(outdir, 'data.txt')
  data = pd.read_table(datafile)
  r = build_ripl(infile = 'regression1.vnt')
  r.infer('(resample 200)')
  # do inference with no data to view prior
  r.infer('(rejection default all 1)')
  this_res = r.infer('(cycle ({0} (peek_all w)) 5)'.format(method))['w']
  out = []
  for j, entry in enumerate(this_res):
    tmp = (pd.DataFrame(entry, columns = ['w1', 'w2']).reset_index().
           rename_axis(dict(index = 'thread'), axis = 1))
    tmp['data_point'] = 0
    tmp['iteration'] = j
    out.append(tmp)
  res.append(pd.concat(out))
  for i, row in data[:7].iterrows():
    print name + ' : ' + str(i)
    r.observe('(y (vector 1 {0}))'.format(row['x']), row['y'])
    this_res = r.infer('(cycle ({0} (peek_all w)) 15)'.format(method))['w']
    out = []
    for j, entry in enumerate(this_res):
      tmp = (pd.DataFrame(entry, columns = ['w1', 'w2']).reset_index().
             rename_axis(dict(index = 'thread'), axis = 1))
      tmp['data_point'] = i
      tmp['iteration'] = j
      out.append(tmp)
    res.append(pd.concat(out))
  with open(path.join(outdir, name + '.pkl'), 'wb') as f:
    pkl.dump(pd.concat(res).reset_index(drop = True), f, protocol = 2)

# runme('mh', '(mh default all 1)')
# runme('hmc', '(hmc default all 0.05 10 1)')
# runme('rejection', '(rejection default all 1)')
# runme('nesterov', '(nesterov default all 0.1 5 1)')

def run_rejection(n_pts):
  '''
  Rejection is too slow; run separately for each set of observations to speed
  things up.
  '''
  start = time.time()
  outdir = path.join(path.dirname(path.realpath(__file__)), 'regression-evolution')
  datafile = path.join(outdir, 'data.txt')
  data = pd.read_table(datafile)
  r = build_ripl(infile = 'regression1.vnt')
  r.infer('(resample 200)')
  for i, row in data[:n_pts].iterrows():
    r.observe('(y (vector 1 {0}))'.format(row['x']), row['y'])
  res = r.infer('(cycle ((rejection default all 1) (peek_all w)) 1)')['w'][0]
  tmp = (pd.DataFrame(res, columns = ['w1', 'w2']).reset_index().
         rename_axis(dict(index = 'thread'), axis = 1))
  tmp['data_point'] = n_pts
  tmp['iteration'] = 0
  with open(path.join(outdir, 'rejection_{0}.pkl'.format(n_pts)), 'wb') as f:
    pkl.dump(tmp, f, protocol = 2)
  print 'Elapsed time for {0} points'.format(n_pts)
  print time.time() - start

# if __name__ == '__main__':
#   n_pts = int(sys.argv[1])
#   run_rejection(n_pts)

def get_results():
  wkdir = path.join(path.dirname(path.realpath(__file__)), 'regression-evolution')
  data = pd.read_table(path.join(wkdir, 'data.txt'))
  results = {}
  for method in ['hmc', 'mh', 'nesterov']:
    with open(path.join(wkdir, method + '.pkl'), 'rb') as f:
      results[method] = pkl.load(f)
  rejection = []
  for i in range(7):
    with open(path.join(wkdir, 'rejection_{0}.pkl'.format(i))) as f:
      rejection.append(pkl.load(f))
  return data, results, rejection

def make_plot(i, j, data, results, rejection, wkdir, counter):
  sns.set_style('white')
  fig, ax = plt.subplots(4, 2, figsize = [8,16])
  these_data = data[:i]
  # plot the different sampling methods
  for k, method in enumerate(['rejection', 'mh', 'hmc', 'nesterov']):
    color = sns.color_palette()[k]
    cmap = convert_to_cmap(color)
    k = k
    if method == 'rejection':
      weights = rejection[i]
    else:
      weights = results[method]
      weights = weights[(weights.data_point == i) & (weights.iteration == j)]
    bw = 1 if (counter > 10 and method == 'nesterov') else 'scott'
    sns.kdeplot(weights[['w1', 'w2']], ax = ax[k, 0], bw = bw,
                cmap = cmap, shade = True)
    ax[k,1].scatter(these_data.x, these_data.y, color = 'black')
    # plot some random lines from the posterior
    plot_weights = weights[0:50:10]
    for _, weight_row in plot_weights.iterrows():
      t = np.r_[-1:1:0.05]
      y = weight_row['w1'] + t * weight_row['w2']
      ax[k,1].plot(t, y, color = color)
    set_limits(ax, k, method)
    # set the title
  title = 'Data point {0}, iteration {1}'.format(i, j)
  fig.suptitle(title)
  fig.savefig(path.join(wkdir, 'posterior_{0}'.format(counter)))
  plt.close(fig)

def convert_to_cmap(color):
    color_rgb = mpl.colors.colorConverter.to_rgb(color)
    colors = [sns.set_hls_values(color_rgb, l=l) for l in np.linspace(1, 0, 12)]
    cmap = sns.blend_palette(colors, as_cmap=True)
    return cmap

def set_limits(ax, k, method):
    ax[k,0].set_title(method)
    ax[k,1].set_title(method)
    ax[k,0].set_xlim([-10,10])
    ax[k,0].set_ylim([-10,10])
    ax[k,1].set_xlim([-1,1])
    ax[k,1].set_ylim([-5,5])

def plot_results():
  # get the data
  wkdir = '/Users/dwadden/code/Venturecxx/examples/ml-models/regression-evolution'
  data, results, rejection = get_results()
  counter = 0
  for i in range(7):
    for j in range(15):
      make_plot(i, j, data, results, rejection, wkdir, counter)
      counter += 1

# plot_results()




