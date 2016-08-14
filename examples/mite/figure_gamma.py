import math
import os
import pickle
import sys
import time

import matplotlib.pyplot as plt
import scipy.special as scipy

import venture.shortcuts as vs

vnts_file = os.path.join(os.path.dirname(__file__), 'figure_gamma.vnts')

def prep():
  r = vs.Mite().make_ripl()
  r.set_mode("venture_script")
  r.execute_program_from_file(vnts_file)
  return r

def gamma_samples(r, shape, ct):
  return [r.evaluate("simulate_std_gamma(%s)" % (shape,)) for _ in range(ct)]

def gamma_assess(r, x, shape):
  return r.evaluate("assess_std_gamma(%s, %s)" % (x, shape))

def gamma_assess2(x, shape):
  ln = (shape - 1) * math.log(x) - x - scipy.gammaln(shape)
  return math.exp(ln)

def save():
  r = prep()
  shape = 2
  n = 1000
  samples = gamma_samples(r, shape, n)
  with open("gamma.sav", "w") as f:
    pickle.dump((shape, samples), f)

def plot():
  with open("gamma.sav", "r") as f:
    (shape, samples) = pickle.load(f)
  n = len(samples)
  nbins = math.floor(math.sqrt(n))
  plt.figure()
  (_counts, bin_edges, _) = plt.hist(samples, bins=nbins)
  points = []
  assessments = []
  def do(place, width):
    points.append(place)
    assessments.append(width * n * gamma_assess2(place, shape))
  for (low, high) in zip(bin_edges, bin_edges[1:]):
    mid = (low+high) / 2
    do(mid, high - low)
  plt.plot(points, assessments)
  plt.show()

def main():
  save()
  plot()


if __name__ == '__main__':
  main()
