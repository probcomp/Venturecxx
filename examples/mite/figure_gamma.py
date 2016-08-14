import math
import os
import pickle
import sys

import numpy as np
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

def gamma_samples2(shape, ct):
  d = shape - 1.0/3
  c = 1.0 / math.sqrt(9 * d)
  def block():
    xs = np.random.normal(size=2*ct)
    cube_root_vs = 1 + c * xs
    vs = cube_root_vs * cube_root_vs * cube_root_vs
    us = np.log(np.random.uniform(size=2*ct))
    return (xs, vs, us)
  ans = []
  while len(ans) < ct:
    for (x, v, u) in zip(*block()):
      if v <= 0: continue
      log_bound = 0.5 * x * x + d * (1 - v)
      if u >= log_bound: continue
      ans.append(d * v)
  return ans

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

def compute_assessment_curve(n, shape, bin_edges):
  bin_width = bin_edges[1] - bin_edges[0]
  scale = n * bin_width # This is area under the histogram
  points = []
  assessments = []
  def do(place):
    points.append(place)
    assessments.append(scale * gamma_assess2(place, shape))
  bot = bin_edges[0]
  top = bin_edges[-1]
  (lowers, step) = np.linspace(bot, top, 100, endpoint=False, retstep=True)
  for place in lowers:
    do(place + step/2.0)
  return (points, assessments)

def plot():
  with open("gamma.sav", "r") as f:
    (shape, samples) = pickle.load(f)
  n = len(samples)
  nbins = math.floor(math.sqrt(n))
  plt.figure()
  (_counts, bin_edges, _) = plt.hist(samples, bins=nbins, label="Sampled frequency", fill=False, linewidth=1)
  (points, assessments) = compute_assessment_curve(n, shape, bin_edges)
  plt.plot(points, assessments, label="Scaled assessment value", linewidth=1, color='red')
  plt.xlabel("Output value")
  plt.ylabel("Frequency")
  plt.title("Simulating the gamma distribution at shape=%3.1f" % (shape,))
  plt.legend(fontsize=19)
  set_font_size(plt.gca(), 22)
  plt.gca().title.set_fontsize(20)
  plt.tight_layout()
  # plt.show()
  plt.savefig("figures/gamma.png")

def set_font_size(ax, size):
    for item in ([ax.title, ax.xaxis.label, ax.yaxis.label] +
                 ax.get_xticklabels() + ax.get_yticklabels()):
        item.set_fontsize(size)

def main():
  if len(sys.argv) == 1:
    save()
    plot()
  elif sys.argv[1] == "save":
    save()
  elif sys.argv[1] == "plot":
    plot()

if __name__ == '__main__':
  main()
