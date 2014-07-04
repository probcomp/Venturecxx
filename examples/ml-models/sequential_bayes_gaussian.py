from venture.shortcuts import (make_puma_church_prime_ripl,
                               make_lite_church_prime_ripl)
import numpy as np, scipy as sp, pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns
from os import path
import os

def runme(outdir):
  techniques = {'hmc' : '(hmc default all 0.05 5 1)',
                'nesterov' : '(nesterov default all 0.1 5 1)',
                'mh' : '(mh default all 1)',
                'rejection' : '(rejection default all 1)'}
  ripls = {technique : make_lite_church_prime_ripl() for technique in techniques}
  for ripl in ripls.values(): ripl.infer('(resample 200)')

  for name, ripl in ripls.items():
    ripl.assume('mu', '(normal 0 10)')
    ripl.assume('x', '(lambda () (normal mu 1))')

  count = 0
  n = 20

  plt.rc('text', usetex = True)

  data = np.random.normal(6, 1, n)
  for ix, datum in enumerate(data):
    these_data = data[:(ix+1)]
    res = {}
    # get the results
    for name, ripl in ripls.items():
      _ = ripl.observe('(x)', datum)
      technique = techniques[name]
      if name == 'rejection':
        this_res = ripl.infer('(cycle ({0} (peek-all mu)) 1)'.format(technique))
        res[name] = np.array(this_res['mu']).ravel()
      else:
        this_res = ripl.infer('(cycle ({0} (peek-all mu)) 5)'.format(technique))
        res[name] = np.array(this_res['mu'])
    # make the plots
    for i in range(5):
      label = 'Data point {0}; Iteration {1}'.format(ix + 1, i + 1)
      print count
      fig, ax = plt.subplots(1)
      sns.kdeplot(res['rejection'], ax = ax, label = 'rejection')
      for technique in ['mh', 'hmc']:
        sns.kdeplot(res[technique][i], ax = ax, label = technique)
      nester = res['nesterov'][i]
      this_bw = 'scott' if count < 10 else 0.05
      sns.kdeplot(res['nesterov'][i], ax = ax, label = 'nesterov', bw = this_bw)
      sns.rugplot(these_data, ax = ax, height = 0.1, color = 'black')
      ax.set_xlim([-0,10])
      ax.set_ylim([0,1.5])
      ax.set_xlabel('\mu')
      ax.set_title(label)
      fig.savefig(path.join(outdir, 'iter_{0}'.format(count)))
      plt.close(fig)
      count += 1

outdir = path.join(path.dirname(path.realpath(__file__)), 'gaussian-evolution')
runme(outdir)
video_name = path.join(outdir, 'inference_comparison.mp4')
template_str = path.join(outdir, 'iter_%d.png')
scale_correction = '"scale=trunc(iw/2)*2:trunc(ih/2)*2"'
os.system('avconv -y -r 5 -i {0} -vf {1} {2}'.format(template_str, scale_correction, video_name))