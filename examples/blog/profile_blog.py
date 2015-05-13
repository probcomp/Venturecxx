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

def main():
  dispatch = {'time' : profile_times,
              'quality' : profile_quality}
  dispatch[argv[1]]()

if __name__ == '__main__':
  main()
