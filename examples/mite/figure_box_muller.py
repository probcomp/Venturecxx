import math
import os
import pickle
import sys

import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats
import scipy.special as scipy

import venture.shortcuts as vs

vnts_file = os.path.join(os.path.dirname(__file__), 'figure_box_muller.vnts')

def prep():
  r = vs.Mite().make_ripl(seed=1)
  r.set_mode("venture_script")
  r.execute_program_from_file(vnts_file)
  return r

def box_muller_samples(r, ct):
  return [r.evaluate("simulate_std_normal()") for _ in range(ct)]

def box_muller_assess(r, x):
  return math.exp(r.evaluate("assess_std_normal(%s)" % (x,)))

def box_muller_samples3(ct):
  return stats.norm.rvs(size=ct)

def box_muller_assess3(x):
  return stats.norm.pdf(x)

def save():
  r = prep()
  n = 10000
  samples = box_muller_samples(r, n)
  with open("box_muller.sav", "w") as f:
    pickle.dump(samples, f)

def compute_assessment_curve(n, bin_edges):
  r = prep()
  bin_width = bin_edges[1] - bin_edges[0]
  scale = n * bin_width # This is area under the histogram
  points = []
  assessments = []
  def do(place):
    points.append(place)
    assessments.append(scale * box_muller_assess(r, place))
  bot = bin_edges[0]
  top = bin_edges[-1]
  (lowers, step) = np.linspace(bot, top, 100, endpoint=False, retstep=True)
  for place in lowers:
    do(place + step/2.0)
  return (points, assessments)

def plot():
  with open("box_muller.sav", "r") as f:
    samples = pickle.load(f)
  n = len(samples)
  nbins = math.floor(math.sqrt(n))
  plt.figure()
  (_counts, bin_edges, _) = plt.hist(samples, bins=nbins, label="Sampled frequency", fill=False, linewidth=1)
  (points, assessments) = compute_assessment_curve(n, bin_edges)
  plt.plot(points, assessments, label="Scaled assessment value", linewidth=1, color='red')
  plt.xlabel("Output value")
  plt.ylabel("Frequency")
  plt.title("Simulating the standard normal distribution")
  plt.legend(fontsize=13)
  set_font_size(plt.gca(), 22)
  plt.gca().title.set_fontsize(20)
  plt.tight_layout()
  # plt.show()
  plt.savefig("figures/box_muller.png")

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
