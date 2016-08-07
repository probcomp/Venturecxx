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
    def stub_trajectory(steps):
      return list(np.cumsum(np.random.normal(0, 0.5, size=steps)))

    return {
      'rmh': [stub_trajectory(100) for _ in range(num_reps)],
      'drift': [stub_trajectory(100) for _ in range(num_reps)]
    }
  else:
    ripl = vs.Mite().make_ripl()
    ripl.execute_program_from_file(vnts_file)
    drift = [ripl.evaluate('traceplot(100)') for _ in range(num_reps)]

    ripl = vs.Mite().make_ripl()
    ripl.execute_program_from_file(vnts_file.replace('drift', 'rmh'))
    rmh = [ripl.evaluate('traceplot(100)') for _ in range(num_reps)]

    return {
      'rmh': rmh,
      'drift': drift
    }

def save(stub=False):
  results = compute_results(12, stub=stub)
  with open("drift.sav", "w") as f:
    pickle.dump(results, f)

def trace_plot(fname, varname, results):
  fig = plt.figure()
  colors = {
    'rmh': 'blue',
    'drift': 'orange'
  }
  for algo, trajectories in results.items():
    color = colors[algo]
    for traj in trajectories:
      x, y = zip(*enumerate(traj))
      plt.plot(x, y, color=color, alpha=0.5)
  [ax] = fig.get_axes()
  ax.set_xlabel("Steps")
  ax.set_ylabel(varname)
  fig.savefig("figures/{}.pdf".format(fname))

def plot():
  with open("drift.sav", "r") as f:
    results = pickle.load(f)
  trace_plot("drift", "x", results)

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
