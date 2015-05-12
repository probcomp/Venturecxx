'''
Examine the asymptotics of inference in BLOG - in particular, poisson-ball.blog
'''

from subprocess import call
from time import time
from functools import partial
from pandas import DataFrame
from multiprocessing import Pool

def profile_one(inference_flag, n):
  method_flag = inference_flag.split('.')[-1]
  blog_file = 'poisson-ball-blog/poisson-ball-{0}.blog'.format(n)
  result_file = 'blog-results/poisson-ball-results-{0}-{1}.json'.format(method_flag, n)
  cmd = ['blog',
         blog_file,
         '-n', '100000',
         '-s', inference_flag,
         '-o', result_file]
  start = time()
  call(cmd)
  elapsed = time() - start
  return elapsed

def profile(inference_flag):
  profile_partial = partial(profile_one, inference_flag)
  workers = Pool(10)
  times = workers.map(profile_partial, range(1,11))
  ds = DataFrame(dict(n_obs_pairs = range(1,11),
                      times= times))
  outname = inference_flag.split('.')[-1]
  ds.to_csv('blog-results/' + outname + '.txt', index = False, sep = '\t')

def main():
  profile('blog.sample.LWSampler')
  profile('blog.sample.MHSampler')

if __name__ == '__main__':
  main()
