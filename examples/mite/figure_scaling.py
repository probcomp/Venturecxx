import os
import pickle
import sys
import time

import matplotlib.pyplot as plt

import venture.shortcuts as vs

vnts_file = os.path.join(os.path.dirname(__file__), 'chain_scaling.vnts')

def timing(trace_type, chain_sizes, num_iters):
  ripl = vs.Mite().make_ripl()
  ripl.execute_program_from_file(vnts_file)
  ans_full = []
  ans_select = []
  for (i, (low, high)) in enumerate(zip([0] + chain_sizes, chain_sizes)):
    if i == 0:
      ripl.define("trace_0", "start_chain(" + str(high) + ", " + trace_type + ")")
    else:
      ripl.define("trace_" + str(i), "extend_chain(%s, %s, trace_%s)" % (low, high, i-1))
    then = time.time()
    ripl.evaluate("go_blank(%s, %s, trace_%s)" % (num_iters, high, i))
    now = time.time()
    blank_time = now - then
    then = time.time()
    ripl.evaluate("go(%s, %s, trace_%s)" % (num_iters, high, i))
    now = time.time()
    ans_full.append(max(now - then - blank_time, 0))
    then = time.time()
    ripl.evaluate("go_select(%s, %s, trace_%s)" % (num_iters, high, i))
    now = time.time()
    ans_select.append(max(now - then - blank_time, 0))
  return (ans_full, ans_select)

def compute_results(stub=False):
  chain_sizes = [5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
  num_iters = 40
  if stub:
    return { "flats": [1, 2, 3, 4], "graphs": [2, 2, 2, 2],
             "chain_sizes": chain_sizes,
             "num_iters": num_iters }
  else:
    (flats, flats_select) = timing("flat_trace", chain_sizes, num_iters)
    (graphs, graphs_select) = timing("graph_trace", chain_sizes, num_iters)
    return { "flats": flats, "graphs": graphs,
             "chain_sizes": chain_sizes,
             "num_iters": num_iters,
             "flats_select": flats_select,
             "graphs_select": graphs_select
    }

def save(stub=False):
  results = compute_results(stub=stub)
  with open("scaling.sav", "w") as f:
    pickle.dump(results, f)

def scale_plot(results):
  flats = results["flats"]
  flats_select = results["flats_select"]
  graphs = results["graphs"]
  graphs_select = results["graphs_select"]
  chain_sizes = results["chain_sizes"]
  num_iters = results["num_iters"]
  plt.figure()
  plt.plot(chain_sizes, [float(f)/num_iters for f in flats], label="Flat table (total)")
  plt.plot(chain_sizes, [float(g)/num_iters for g in graphs], label="Dependency graph (total)")
  plt.plot(chain_sizes, [float(f)/num_iters for f in flats_select],
           label="Flat table (selection)")
  plt.plot(chain_sizes, [float(g)/num_iters for g in graphs_select],
           label="Dependency graph (selection)")
  plt.xlabel("Number of timesteps")
  plt.ylabel("Time per transition (s)")
  plt.title("Inference speed scaling on an HMM")
  plt.legend(fontsize=19, loc='best')
  set_font_size(plt.gca(), 20)
  plt.gcf().subplots_adjust(bottom=0.17, left=0.16)
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
