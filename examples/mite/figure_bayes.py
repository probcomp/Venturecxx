import pickle
import sys
import time
from collections import OrderedDict

import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
import seaborn

import venture.shortcuts as vs

vnts_file = __file__.rsplit('.', 1)[0] + '.vnts'

def compute_results(resolution, stub=False):
  x = np.linspace(-1, 5, resolution)
  if stub:
    y = 4.0
    px = stats.norm(0, 1).logpdf(x)
    pygx = stats.norm(x, 1).logpdf(y)
    x_mc = stats.norm(0, 1).rvs((500, len(x)))
    py = np.log(np.mean(stats.norm(x_mc, 1).pdf(y), axis=0))
    return (x, px + pygx - py)
  else:
    ripl = vs.Mite().make_ripl()
    ripl.execute_program_from_file(vnts_file)
    pxgy = [
      ripl.evaluate("normal_normal_posterior_density({})".format(xi))
      for xi in x
    ]
    return (x, pxgy)

def save(stub=False):
  results = compute_results(50, stub=stub)
  with open("bayes_normal_normal.sav", "w") as f:
    pickle.dump(results, f)

def density_plot(fname, results):
  (x, y) = results
  xx = np.linspace(x[0], x[-1], 200)
  fig = plt.figure()
  plt.plot(xx, stats.norm(2, 0.5**0.5).pdf(xx), label="Analytic", linewidth=1, color='red')
  plt.scatter(x, np.exp(y), label="Estimated", color='black', marker='.')
  plt.legend(loc='lower right')
  plt.xlabel('x')
  plt.ylabel('Probability density')
  plt.title('Estimated posterior density p(x | y = 4.0)')
  fig.savefig("figures/{}.pdf".format(fname))

def plot():
  with open("bayes_normal_normal.sav", "r") as f:
    results = pickle.load(f)
  density_plot("bayes_normal_normal", results)

if __name__ == '__main__':
  if len(sys.argv) == 1:
    save()
    plot()
  elif sys.argv[1] == "save":
    save()
  elif sys.argv[1] == "plot":
    plot()
  elif sys.argv[1] == "stub":
    save(stub=True)
    plot()
