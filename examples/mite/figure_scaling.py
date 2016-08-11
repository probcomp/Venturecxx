import os
import pickle
import sys
import time

import matplotlib.pyplot as plt

import venture.shortcuts as vs

vnts_file = os.path.join(os.path.dirname(__file__), 'chain_scaling.vnts')

chain_sizes = [5, 10, 20, 50]

def timing(trace_type, num_iters):
  ripl = vs.Mite().make_ripl()
  ripl.execute_program_from_file(vnts_file)
  ans = []
  for (i, (low, high)) in enumerate(zip([0] + chain_sizes, chain_sizes)):
    if i == 0:
      ripl.define("trace_0", "start_chain(" + str(high) + ", " + trace_type + ")")
    else:
      ripl.define("trace_" + str(i), "extend_chain(%s, %s, trace_%s)" % (low, high, i-1))
    then = time.time()
    ripl.evaluate("go(%s, trace_%s)" % (num_iters, i))
    now = time.time()
    ans.append(now - then)
  return ans

def compute_results(num_iters, stub=False):
  if stub:
    return { "flats": [1, 2, 3, 4], "graphs": [2, 2, 2, 2] }
  else:
    flats = timing("flat_trace", num_iters)
    graphs = timing("graph_trace", num_iters)
    return { "flats": flats, "graphs": graphs }

def save(stub=False):
  results = compute_results(10, stub=stub)
  with open("scaling.sav", "w") as f:
    pickle.dump(results, f)

def scale_plot(results):
  flats = results["flats"]
  graphs = results["graphs"]
  plt.figure()
  plt.plot(chain_sizes, flats, label="Flat table")
  plt.plot(chain_sizes, graphs, label="Dependency graph")
  plt.xlabel("Number of timesteps")
  plt.ylabel("Time (s)")
  plt.title("Inference speed scaling on an HMM")
  plt.legend(fontsize=25)
  set_font_size(plt.gca(), 25)
  plt.savefig("figures/scaling.pdf")
  # plt.show()

def set_font_size(ax, size):
    for item in ([ax.title, ax.xaxis.label, ax.yaxis.label] +
                 ax.get_xticklabels() + ax.get_yticklabels()):
        item.set_fontsize(size)

def plot():
  with open("scaling.sav", "r") as f:
    results = pickle.load(f)
  scale_plot(results)

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
