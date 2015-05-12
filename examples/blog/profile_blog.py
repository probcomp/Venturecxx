'''
Examine the asymptotics of inference in BLOG - in particular, poisson-ball.blog
'''

from subprocess import call, Popen
from time import time
from functools import partial
from pandas import DataFrame
from sys import argv

def profile_one(inference_flag, parallelize, n):
  method_flag = inference_flag.split('.')[-1]
  blog_file = 'poisson-ball-blog/poisson-ball-{0}.blog'.format(n)
  result_file = 'blog-results/poisson-ball-results-{0}-{1}.json'.format(method_flag, n)
  cmd = ['blog',
         blog_file,
         '-n', '100000',
         '-s', inference_flag,
         '-o', result_file]
  system_call = Popen if parallelize else call
  start = time()
  system_call(cmd)
  elapsed = time() - start
  return elapsed

def profile(inference_flag, parallelize):
  times = map(partial(profile_one, inference_flag, parallelize), range(1,11))
  ds = DataFrame(dict(n_obs_pairs = range(1,11),
                      times= times))
  outname = inference_flag.split('.')[-1]
  ds.to_csv('blog-results/' + outname + '.txt', index = False, sep = '\t')

def main():
  if len(argv) > 1:
    parallelize = eval(argv[1])
  else:
    parallelize = True
  profile('blog.sample.LWSampler', parallelize)
  profile('blog.sample.MHSampler', parallelize)

if __name__ == '__main__':
  main()
