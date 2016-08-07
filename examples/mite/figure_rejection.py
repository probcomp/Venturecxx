import pickle
import sys

import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
import seaborn

import venture.shortcuts as vs

vnts_file = __file__.rsplit('.', 1)[0] + '.vnts'

def compute_results(num_reps, stub=False):
  if stub:
    return {
      'posterior': list(np.random.normal(2, 0.7, size=num_reps)),
      'prior': list(np.random.normal(0, 1, size=num_reps)),
    }
  else:
    ripl = vs.Mite().make_ripl()
    ripl.execute_program_from_file(vnts_file)

    return {
      'prior': [ripl.evaluate('example_prior()') for _ in range(num_reps)],
      'posterior': [ripl.evaluate('example_posterior()') for _ in range(num_reps)],
    }

def save(stub=False):
  results = compute_results(500, stub=stub)
  with open("rejection.sav", "w") as f:
    pickle.dump(results, f)

def prior_posterior_plot(fname, varname, results):
  fig, [ax1, ax2] = plt.subplots(2, 1, sharex=True)
  xmin = -5
  xmax = 5
  # plot the prior
  seaborn.distplot(
    results['prior'], ax=ax1,
    kde=False, rug=True, norm_hist=True)
  support = np.linspace(xmin, xmax, 200)
  density = stats.norm(0, 1).pdf(support)
  ax1.plot(support, density, color='orange', alpha=0.5)
  ax1.set_title('Prior')
  # plot the posterior
  seaborn.distplot(
    results['posterior'], ax=ax2,
    kde=False, rug=True, norm_hist=True)
  density = stats.norm(2, 0.5**0.5).pdf(support)
  ax2.plot(support, density, color='orange', alpha=0.5)
  ax2.set_title('Posterior')
  # save
  ax2.set_xlim(xmin, xmax)
  ax2.set_xlabel(varname)
  fig.savefig("figures/{}.pdf".format(fname))

def plot():
  with open("rejection.sav", "r") as f:
    results = pickle.load(f)
  prior_posterior_plot("rejection", "x", results)

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
