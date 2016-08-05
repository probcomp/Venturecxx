import pickle
import sys

import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
import seaborn

import venture.shortcuts as vs

def compute_results(num_reps, stub=False):
  if stub:
    def stub_mh(steps):
      x = np.random.normal(0, 1, size=steps)
      weight = stats.norm(x, 1).pdf(4)
      return np.random.choice(x, p=weight/weight.sum())

    return {
      5: [stub_mh(5) for _ in range(num_reps)],
      20: [stub_mh(20) for _ in range(num_reps)],
      100: [stub_mh(100) for _ in range(num_reps)],
    }
  else:
    ripl = vs.Mite().make_ripl()
    ripl.execute_program_from_file(__file__.replace('.py', '.vnts'))

    return {
      5: [ripl.evaluate('resimulation_mh(5)') for _ in range(num_reps)],
      20: [ripl.evaluate('resimulation_mh(20)') for _ in range(num_reps)],
      100: [ripl.evaluate('resimulation_mh(100)') for _ in range(num_reps)],
    }

def save(stub=False):
  results = compute_results(500, stub=stub)
  with open("rmh.sav", "w") as f:
    pickle.dump(results, f)

def prior_posterior_plot(fname, varname, results):
  fig, axes = plt.subplots(3, 1, sharex=True)
  xmin = -5
  xmax = 5
  # plot each number of steps
  for ax, steps in zip(axes, [5, 20, 100]):
    seaborn.distplot(
      results[steps], ax=ax,
      kde=False, rug=True, norm_hist=True)
    support = np.linspace(xmin, xmax, 200)
    density = stats.norm(2, 0.5**0.5).pdf(support)
    ax.plot(support, density, color='#ccb974')
    ax.set_title('Resimulation MH (steps = {})'.format(steps))
  # save
  axes[-1].set_xlim(xmin, xmax)
  axes[-1].set_xlabel(varname)
  fig.savefig("figures/{}.pdf".format(fname))

def plot():
  with open("rmh.sav", "r") as f:
    results = pickle.load(f)
  prior_posterior_plot("rmh", "x", results)

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
