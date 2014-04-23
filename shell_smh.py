from venture.shortcuts import *
from venture.unit import VentureUnit
from subprocess import call

T = 3
seed = 3
port = 5013
ripl = make_lite_church_prime_ripl()

def initMatlab():
  call(['matlab', '-r', 'cd C:\\Shell_cleaned_05182014\\Shell_reformulated_5010\\Matlab_code;open_wormhole(%d)' % port])
  matlab = True

def garbageCollect():
  current_files = [ripl.sample("(get_state %d)" % t) for t in range(0, T+1)] + [ripl.sample("(get_emission %d)" % t) for t in range(1, T+1)]
  current_files = [str(int(file)) + ".mat" for file in current_files]
  folder = "../Matlab_code/states_%d/" % seed
  import os
  files = os.listdir(folder)
  for file in files:
    if file not in current_files:
      os.remove(folder + file)
  
def run():
  print "Starting run."
  ripl.clear()
  ripl.assume("sim","(make_simulator %d %d)" % (seed, port))
  ripl.assume("get_params","""
  (mem (lambda (t) (scope_include 0 t                                                                                       
    (array (uniform_continuous 0 1)                                                                              
           (uniform_continuous 0 1)                               
           (uniform_continuous 0 1)                                                                              
           (uniform_continuous 0 1)                                                                              
           (uniform_continuous 0 1)))))
  """)
  ripl.assume("get_state","""                                                                                    
  (mem (lambda (t)
  (if (= t 0)
    (sim (quote initialize))
    (sim (quote simulate) (get_state (- t 1)) (get_params t)))))
  """)

  ripl.assume("get_emission","""
  (mem (lambda (t)
  (sim (quote emit) (get_state t))))
  """)

  ripl.assume("get_distance","(mem (lambda (t) (sim (quote distance) (get_emission t))))")
  
  logscores = []

  for t in range(1, T+1):
    ripl.observe("(log_flip (get_distance %d))" % t,"true")
    
    logscores.append([])
    for i in range(t):
      ripl.infer("(mh 0 one %d)" % 2)
      garbageCollect()
      logscores[-1].append(ripl.get_global_logscore())
  
  return logscores

runs = [run() for i in range(2)]

import pickle
pickle.dump(runs, open("smh_logscores", "wb"))