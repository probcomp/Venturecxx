import scipy
import numpy as np
import pandas as pd
from os.path import join, exists
import os
from shutil import rmtree
from matplotlib import pyplot as plt

from venture.lite.discrete import DiscretePSP
from venture.lite import value as v
from venture.lite.builtin import typed_nr
import venture.ripl.utils as u

def __venture_start__(ripl):
  ripl = bind_poisson(ripl)
  ripl.bind_callback('query_diversify', query_diversify)
  ripl.bind_callback('query_rejection', query_rejection)
  ripl.bind_callback('plot_state', plot_state)
  ripl.bind_callback('state_video', state_video)
  ripl.bind_callback('assert_nballs', assert_nballs)
  ripl.bind_callback('assert_nballs_resample', assert_nballs_resample)

################################################################################

# Evaluating inference methods for comparison with BLOG

class BoundedPoissonOutputPSP(DiscretePSP):
  def simulate(self,args):
    return min(scipy.stats.poisson.rvs(args.operandValues[0]), 20)
  def logDensity(self,val,args):
    if val < 20:
      return scipy.stats.poisson.logpmf(val,args.operandValues[0])
    else: return np.log(1 - sum(scipy.stats.poisson.pmf(np.r_[0:20],args.operandValues[0])))
  def enumerateValues(self,args):
    return range(0,21)
  def description(self,name):
    return "  (%s lambda) samples a poisson with rate lambda" % name

def bind_poisson(ripl):
  'Bind a version of the Poisson that returns NumberType instead of CountType'
  poisson = typed_nr(BoundedPoissonOutputPSP(), [v.PositiveType()], v.CountType())
  ripl.bind_foreign_sp('bounded_poisson', poisson)
  return ripl

def query_diversify(inferrer, nballs):
  res = pd.Series(inferrer.particle_normalized_probs(), u.strip_types(nballs))
  print 'The posterior probabilities from enumerative_diversify are:'
  print res

def query_rejection(inferrer):
  ds = inferrer.result.dataset()
  ix = np.r_[0:21]
  counts = ds['nballs'].value_counts()[ix].fillna(0)
  posterior = counts / sum(counts)
  posterior.name = 'probability'
  posterior.index.name = 'nballs'
  print 'The posterior probabilities from rejection sampling are:'
  print posterior
  pd.DataFrame(posterior).to_csv('blog_rejection_posterior.txt', sep = '\t',
                                 float_format = '%0.4f')

################################################################################

# Code to test that we get a number of balls consistent with the number of
# observations
def assert_nballs(inferrer, min_balls):
  '''
  Tests that the posterior is consistent with the observations - for instance,
  if two balls of different color are observed without noise, there must be
  at least two balls in the urn
  '''
  assert inferrer.result.dataset().nballs.min() >= u.strip_types(min_balls)

def assert_nballs_resample(_, nballs, min_nballs):
  "For resampling, we don't get the number of balls from the inferrer"
  assert min(u.strip_types(nballs)) >= u.strip_types(min_nballs)[0]

################################################################################

# Code to create video of the current state in the MH chain

OUT = '/Users/dwadden/Google Drive/probcomp/challenge-problems/problem-4/poisson_mh_debug'

def state_video(_, label):
  label = unwrap(label)
  figdir = join(OUT, label)
  fig_regex = join(figdir, 'sweep_%1d.png')
  video_name = join(OUT, label + '.mp4')
  cmd = 'avconv -y -r 5 -i "{0}" "{1}"'.format(fig_regex, video_name)
  os.system(cmd)

def plot_state(inferrer, n_obs, in_urn, colors, label):
  n_obs = int(unwrap(n_obs))
  in_urn = unwrap(in_urn)
  colors = unwrap(colors)
  label = unwrap(label)
  fig, ax = plot_setup(label)
  plot_observed(n_obs, ax)
  plot_latent(in_urn, colors, ax)
  count = inferrer.result.sweep - 1
  figdir = join(OUT, label)
  if not count:
    if exists(figdir):
      rmtree(figdir)
    os.mkdir(figdir)
  figpath = join(figdir, 'sweep_' + str(count) + '.png')
  fig.savefig(figpath)
  plt.close(fig)

def plot_setup(label):
  fig, ax = plt.subplots(figsize = [12, 3])
  fig.subplots_adjust(left = 0.3, top = 0.8)
  ax.set_xticks([])
  ax.set_xlim([-0.05,1.05])
  ax.set_ylim([-0.05,0.85])
  ax.set_title(label)
  ax.text(-0.15, 0.2,
          'Pool of possible balls\nStarred balls are currently in urn',
          verticalalignment = 'center', horizontalalignment = 'right')
  ax.text(-0.15, 0.6, 'Observed draws from urn',
          verticalalignment = 'center', horizontalalignment = 'right')
  return fig, ax

def unwrap(wrapped): return u.strip_types(wrapped)[0]

def plot_observed(n_obs, ax):
  observed_colors = [1, 0, 1, 0, 1, 0]
  for i in range(n_obs):
    ax.plot(get_x(i), 0.6, 'o',
            color = get_color(observed_colors[i]),
            markersize = 12)

def plot_latent(in_urn, colors, ax):
  plot_balls(colors, ax)
  plot_markers(in_urn, ax)

def plot_balls(colors, ax):
  for i, color in enumerate(colors):
    ax.plot(get_x(i), 0.2,'o',
            color = get_color(color),
            markersize = 12)

def plot_markers(in_urn, ax):
  for marker in in_urn:
    if marker < 20:
      ax.plot(get_x(marker), 0.3, '*',
              color = 'black', markersize = 12)

def get_x(i):
  return np.linspace(0,1,20)[i]

def get_color(n): return 'blue' if n else 'green'
