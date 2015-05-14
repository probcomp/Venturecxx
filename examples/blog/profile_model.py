'''
Examine the asymptotics of inference in BLOG - in particular, poisson-ball.blog
'''

from subprocess import call
from time import time
from functools import partial
from pandas import DataFrame
from multiprocessing import Pool
from sys import argv
import numpy as np
from scipy import stats
import json
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

def run_one(inference_flag, out, n_iter, n_obs):
  method_flag = inference_flag.split('.')[-1]
  blog_file = 'poisson-ball-blog/poisson-ball-{0}.blog'.format(n_obs)
  result_file = out + '/' + 'poisson-ball-results-{0}-{1}-{2}.json'.format(method_flag, n_iter, n_obs)
  cmd = ['blog',
         blog_file,
         '-n', n_iter,
         '-s', inference_flag,
         '-o', result_file]
  start = time()
  call(cmd)
  elapsed = time() - start
  return elapsed

def profile_time(inference_flag):
  profile_partial = partial(run_one, inference_flag, 'blog-profile-time', '100000')
  workers = Pool(10)
  times = workers.map(profile_partial, range(1,11))
  ds = DataFrame(dict(n_obs_pairs = range(1,11),
                      times= times))
  outname = inference_flag.split('.')[-1]
  ds.to_csv('blog-profile-time/' + outname + '.txt', index = False, sep = '\t')

def profile_times():
  profile_time('blog.sample.LWSampler')
  profile_time('blog.sample.MHSampler')

def profile_quality():
  # Can't parallelize b/c python sucks at higher-order functions
  profile_partial = partial(run_one, inference_flag = 'blog.sample.LWSampler',
                            out = 'profile-quality', n_obs = 5)
  _ = [profile_partial(n_iter = n_iter)
       for n_iter in [str(int(x)) for x in np.logspace(3, 5, 10)]]

def compare_quality():
  'Compare quality of likelihood weighting in Venture and Blog'
  n_iters = [1000,1668,2782,4641,7742,12915,21544,35938,59948,100000]
  divergences = pd.DataFrame(map(compute_divergences, n_iters))
  divergences.index = n_iters
  fig, ax = plt.subplots(1)
  divergences.plot(ax = ax, logx = True,
                   title = 'Inference quality in poisson-ball model: BLOG and Venture')
  ax.set_xlabel('# iterations (log scale)')
  ax.set_ylabel('KL divergence')
  fig.savefig('profile-quality/poisson-ball-kl-divergence.png')
                   
def compute_divergences(n_iter):
  'Compute divergences between Venture, Blog, and ground truth after n_iter samples'
  exact_posterior = get_exact_posterior()
  venture_posterior = get_venture_posterior(n_iter)
  blog_posterior = get_blog_posterior(n_iter)
  return {'exact_venture' : kl(exact_posterior, venture_posterior),
          'exact_blog'    : kl(exact_posterior, blog_posterior),
          'venture_blog'  : kl(venture_posterior, blog_posterior)}

def kl(ps, qs):
  def enough_supported(xs, ix): return xs[ix].sum() / xs.sum() > 0.99
  # For KL to work, support of distributions must be identical
  # Index out any entries for which only 1 distribution has support
  # Check that such entries constitute less than 1% of the support
  ix = ps.index.intersection(qs.index)
  if enough_supported(ps, ix) and enough_supported(qs, ix):
    return stats.entropy(ps[ix], qs[ix])
  else:
    return np.inf

def get_exact_posterior():
  return pd.read_csv('profile-quality/poisson-ball-exact-posterior-5.csv',
                     index_col = 'n_balls')['p']

def get_venture_posterior(n_iter):
  ds = pd.read_csv('profile-quality/poisson-ball-results-venture.csv',
                   nrows = n_iter)
  ds['n_balls'] = ds['n_balls'].apply(int)
  ds['particle weight'] = ds['particle log weight'].apply(np.exp)
  ps = ds.groupby('n_balls').agg({'particle weight' : sum})['particle weight']
  ps.name = 'venture'
  return ps

def get_blog_posterior(n_iter):
  f_name = 'profile-quality/poisson-ball-results-LWSampler-{0}-5.json'.format(n_iter)
  with open(f_name) as f:
    xs = json.load(f)
  logps = pd.Series(dict(xs[0][1])).convert_objects(convert_numeric = True)
  logps.index = map(int, logps.index)
  ps = np.exp(logps).sort_index()
  ps.name = 'blog'
  return ps

def main():
  dispatch = {'time' : profile_times,
              'quality' : profile_quality,
              'compare' : compare_quality}
  dispatch[argv[1]]()

if __name__ == '__main__':
  main()
  
