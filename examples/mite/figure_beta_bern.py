import pickle
import sys
import time

import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
import seaborn

import venture.shortcuts as vs

vnts_file = __file__.rsplit('.', 1)[0] + '.vnts'

def compute_results(num_reps, stub=False):
  if stub:
    def stub_collapsed(_steps):
      return {'time': np.random.normal(2, 0.2),
              'measurement': -4.4465}
    def stub_proc(steps):
      return {'time': np.random.normal(1 + steps, 0.2),
              'measurement': np.log(np.random.beta(np.exp(-4.4465) * 10 * (1 + steps), 10 * (1 + steps)))}

    ret = {}
    infer_programs = {
      'collapsed': [(stub_collapsed, 0)],
      'proc': [(stub_proc, steps) for steps in [0, 1, 2, 4, 8]]
    }
    for variant in ['collapsed', 'proc']:
      for infer in infer_programs[variant]:
        (f, steps) = infer
        ret[variant, steps] = [f(steps) for _ in range(num_reps)]
    return ret
  else:
    ripl = vs.Mite().make_ripl()
    ripl.execute_program_from_file(vnts_file)
    def time_and_result(beta_bern, infer):
      string = '''\
example_beta_bern(make_beta_bern_{},
  () -> {})
'''.format(beta_bern, infer)
      then = time.time()
      result = ripl.evaluate(string)
      now = time.time()
      return {'time': now - then, 'measurement': result}
    ret = {}
    infer_programs = {
      'collapsed': ['pass'],
      'uncollapsed': ['conjugate_gibbs_infer()'],
      'proc': ['repeat({}, resimulation_infer())'.format(steps)
               for steps in [0, 1, 2, 4, 8]]
    }
    for variant in ['collapsed', 'uncollapsed', 'proc']:
      for infer in infer_programs[variant]:
        ret[variant, infer] = [
          time_and_result(variant, infer)
          for _ in range(num_reps)]
    return ret

def save(stub=False):
  results = compute_results(50, stub=stub)
  with open("beta_bern.sav", "w") as f:
    pickle.dump(results, f)

def timeplot(fname, results):
  fig = plt.figure()
  colors = {
    'collapsed': 'blue',
    'uncollapsed': 'yellow',
    'proc': 'green'
  }
  # plot each kind
  for (variant, _steps), measurements in results.items():
    times = [m['time'] for m in measurements]
    weights = [m['measurement'] for m in measurements]
    plt.scatter(times, weights,
                color=colors[variant],
                label=variant,
                alpha=0.7)
  plt.xlabel('Time')
  plt.ylabel('Observation log weight')
  fig.savefig("figures/{}.pdf".format(fname))

def plot():
  with open("beta_bern.sav", "r") as f:
    results = pickle.load(f)
  timeplot("beta_bern", results)

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
