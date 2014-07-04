from venture.venturemagics.ip_parallel import MRipl
import numpy as np, scipy as sp, pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns
from os import path

def runme(outdir):
  techniques = {'hmc' : '(hmc default all 0.05 5 1)',
                'nesterov' : '(nesterov default all 0.1 5 1)',
                'mh' : '(mh default all 1)',
                'rejection' : '(rejection default all 1)'}
  ripls = {technique : MRipl(256, 'lite', False) for technique in techniques}

  for name, ripl in ripls.items():
    ripl.assume('mu', '(normal 0 10)')
    ripl.assume('x', '(lambda () (normal mu 1))')

  count = 0
  n = 10

  data = np.random.normal(6, 1, n)
  for datum in data:
    res = {}
    # get the results
    for name, ripl in ripls.items():
      _ = ripl.observe('(x)', datum)
      technique = techniques[name]
      if name == 'rejection':
        this_res = ripl.infer('(cycle ({0} (peek mu)) 1)'.format(technique))
        res[name] = np.array([x['mu'] for x in this_res]).ravel()
      else:
        this_res = ripl.infer('(cycle ({0} (peek mu)) 5)'.format(technique))
        res[name] = np.array([x['mu'] for x in this_res]).T
    # make the plots
    for i in range(n):
      print count
      fig, ax = plt.subplots(1)
      sns.distplot(res['rejection'], ax = ax, label = 'rejection', hist = False)
      for technique in ['mh', 'hmc', 'nesterov']:
        sns.distplot(res[technique][i], ax = ax, label = technique, hist = False)
      ax.set_xlim([-5,10])
      ax.set_ylim([0,2])
      fig.savefig(path.join(outdir, 'iter_{0}'.format(count)))
      plt.close(fig)
      count += 1

outdir = path.join(path.dirname(path.realpath(__file__)), 'gaussian-evolution')
runme(outdir)
