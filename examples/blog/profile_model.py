'''
Examine the asymptotics of inference in BLOG - in particular, poisson-ball.blog
'''

from itertools import product
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

def profile_time_blog(inference_flag):
  profile_partial = partial(run_one, inference_flag, 'blog-profile-time', '100000')
  workers = Pool(10)
  times = workers.map(profile_partial, range(1,11))
  ds = DataFrame(dict(n_obs_pairs = range(1,11),
                      times= times))
  outname = inference_flag.split('.')[-1]
  ds.to_csv('blog-profile-time/' + outname + '.txt', index = False, sep = '\t')

def profile_times_blog():
  profile_time_blog('blog.sample.LWSampler')
  profile_time_blog('blog.sample.MHSampler')

def profile_quality_blog():
  # Can't parallelize b/c python sucks at higher-order functions
  profile_partial = partial(run_one, inference_flag = 'blog.sample.LWSampler',
                            out = 'profile-quality', n_obs = 5)
  _ = [profile_partial(n_iter = n_iter)
       for n_iter in [str(int(x)) for x in np.logspace(3, 5, 10)]]

def profile_quality_venture():
  set_fun_names = ["'prefix_k", "'set_as_list"]
  inference_fun_names = ["lw", "mh"]
  for set_fun_name, inference_fun_name in product(set_fun_names, inference_fun_names):
    profile_quality_venture_loop(set_fun_name, inference_fun_name)

def profile_quality_venture_loop(set_fun_name, inference_fun_name):
  def get_inference_fun(inference_fun_name):
    return {"lw" : "(lambda () (likelihood_weight))",
            "mh" : "(lambda () (mh default one 1))"}[inference_fun_name]
  inference_fun = get_inference_fun(inference_fun_name)
  file_name = ('\'symbol<"profile-quality/poisson-ball-results-venture-{0}-{1}-5">'.
               format(set_fun_name.replace("'", ""), inference_fun_name))
  inf_cmd = ('[infer (profile_quality (list {0} {1} {2}))]'.
             format(set_fun_name, inference_fun, file_name))
  call(["venture", "lite", "-P",
        "-L", "poisson_ball.py",
        "-f", "poisson_ball.vnt",
        "-f", "profile_model.vnt",
        "-e", inf_cmd])

def compare_quality():
  'Compare quality of likelihood weighting in Venture and Blog'
  n_iters = [1000,1668,2782,4641,7742,12915,21544,35938,59948,100000]
  pairs  = map(compute_divergences, n_iters)
  kls = pd.DataFrame([pair[0] for pair in pairs], index = n_iters)
  ts = pd.DataFrame([pair[1] for pair in pairs], index = n_iters)
  fig, axs = plt.subplots(2,2,figsize = (12,8))
  lw_idx = ['prefix_k-lw', 'set_as_list-lw']
  mh_idx = ['prefix_k-mh', 'set_as_list-mh']
  fig = kl_vs_iter(kls[lw_idx + ['blog']], fig, axs[0,0])
  fig = kl_vs_iter(kls[mh_idx], fig, axs[1,0])
  fig = kl_vs_time(kls[lw_idx], ts[lw_idx], fig, axs[0,1])
  fig = kl_vs_time(kls[mh_idx], ts[mh_idx], fig, axs[1,1])
  fig.suptitle('Inference quality in poisson-ball model: BLOG and Venture')
  fig.savefig('profile-quality/poisson-ball-inference-quality.png')

def kl_vs_iter(kls, fig, ax):
  kls.plot(ax = ax, logx = True)
  if ax.is_last_row(): ax.set_xlabel('# iterations (log scale)')
  if ax.is_first_col(): ax.set_ylabel('KL divergence')
  return fig

def kl_vs_time(kls, ts, fig, ax):
  for label in ts:
    ax.plot(ts[label], kls[label], label = label)
  ax.set_xscale('log')
  ax.legend()
  if ax.is_last_row(): ax.set_xlabel('Wall time (log seconds)')
  if ax.is_first_col(): ax.set_ylabel('KL divergence')
  return fig

def compute_divergences(n_iter):
  'Compute divergences between Venture, Blog, and ground truth after n_iter samples'
  exact_posterior = get_exact_posterior()
  ps, ts = get_venture_posteriors(n_iter)
  ps['blog'] = get_blog_posterior(n_iter)
  kls = {key : kl(exact_posterior, value) for key, value in ps.iteritems()}
  return kls, ts

def kl(ps, qs):
  # For KL to work, support of distributions must be identical
  # Index out any entries for which only 1 distribution has support
  # Check that such entries constitute less than 1% of the support
  def drop_no_support(xs): return xs.replace(0, np.nan).dropna()
  def enough_supported(xs, ix): return xs[ix].sum() / xs.sum() > 0.99
  ps = drop_no_support(ps)
  qs = drop_no_support(qs)
  ix = ps.index.intersection(qs.index)
  if enough_supported(ps, ix) and enough_supported(qs, ix):
    return stats.entropy(ps[ix], qs[ix])
  else:
    return np.inf

def get_exact_posterior():
  return pd.read_csv('profile-quality/poisson-ball-exact-posterior-5.csv',
                     index_col = 'n_balls')['p']

def get_venture_posteriors(n_iter):
  path_prefix = 'profile-quality/poisson-ball-results-venture-'
  xs = map(partial(get_venture_posterior, n_iter),
           [path_prefix + x for x in ["prefix_k-lw-5.csv",
                                      "prefix_k-mh-5.csv",
                                      "set_as_list-lw-5.csv",
                                      "set_as_list-mh-5.csv"]])
  ts = dict([(x[0], x[2]) for x in xs])
  ps = dict([(x[0], x[1]) for x in xs])
  return ps, ts

def get_venture_posterior(n_iter, f_name):
  ds = pd.read_csv(f_name, nrows = n_iter)
  name = '-'.join(f_name.split('-')[-3:-1])
  ds['n_balls'] = ds['n_balls'].apply(int)
  ds['particle weight'] = ds['particle log weight'].apply(np.exp)
  ps = ds.groupby('n_balls').agg({'particle weight' : sum})['particle weight']
  ps.name = name
  elapsed_t = max(ds['time (s)']) - min(ds['time (s)'])
  return name, ps, elapsed_t

def get_blog_posterior(n_iter):
  f_name = 'profile-quality/poisson-ball-results-LWSampler-{0}-5.json'.format(n_iter)
  with open(f_name) as f:
    xs = json.load(f)
  logps = pd.Series(dict(xs[0][1])).convert_objects(convert_numeric = True)
  logps.index = map(int, logps.index)
  ps = np.exp(logps).sort_index()
  ps.name = 'blog'
  return ps

def profile_times_venture():
  set_fun_names = ["'prefix_k", "'set_as_list"]
  inference_fun_names = ["lw", "mh"]
  for set_fun_name, inference_fun_name in product(set_fun_names, inference_fun_names):
    profile_time_venture(set_fun_name, inference_fun_name)

def profile_time_venture(set_fun_name, inference_fun_name):
  print set_fun_name + ' ' + inference_fun_name
  def get_inference_fun(inference_fun_name):
    return {"lw" : "(lambda () (likelihood_weight))",
            "mh" : "(lambda () (mh default one 1))"}[inference_fun_name]
  inference_fun = get_inference_fun(inference_fun_name)
  profile_partial = partial(run_one_venture, set_fun_name, inference_fun)
  workers = Pool(10)
  times = workers.map(profile_partial, range(1, 11))
  ds = pd.DataFrame(dict(n_obs_pairs = range(1,11),
                         times = times))
  outname = set_fun_name.replace("'", "") + '-' + inference_fun_name
  ds.to_csv('venture-profile-time/' + outname + '.txt',
            index = False, sep = '\t')

def run_one_venture(set_fun_name, inference_fun, n_obs):
  inf_cmd = ('[infer (profile_time (list {0} {1} {2}))]'.
             format(n_obs, set_fun_name, inference_fun))
  print inf_cmd
  start = time()
  call(["venture", "lite", "-P",
        "-L", "poisson_ball.py",
        "-f", "poisson_ball.vnt",
        "-f", "profile_model.vnt",
        "-e", inf_cmd])
  elapsed = time() - start
  return elapsed

def main():
  dispatch = {'time_blog' : profile_times_blog,
              'time_venture' : profile_times_venture,
              'quality_blog' : profile_quality_blog,
              'quality_venture' : profile_quality_venture,
              'compare' : compare_quality}
  dispatch[argv[1]]()

if __name__ == '__main__':
  main()
