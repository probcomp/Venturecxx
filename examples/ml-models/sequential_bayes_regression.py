'''
Illustrates sequential Bayesian updating in Venture, for linear regression
model in 2 dimensions
'''

from __future__ import division
from venture.unit import Analytics, MRipl
import re
from venture.shortcuts import (make_puma_church_prime_ripl,
                               make_lite_church_prime_ripl)
import pandas as pd

def make_data():
  w = matrix([0.5, -0.25]).T
  sigma_2 = 0.25
  X = matrix(np.random.uniform(-1, 1, size = [20,2]))
  y = matrix(np.random.normal(X * w, np.sqrt(sigma_2)))
  return {'X' : X, 'y' : y, 'w' : w, 'sigma_2' : sigma_2}

def load_model(infile):
  with open(infile) as f:
    lines = [x.strip() for x in f.readlines()]
  pass_next = False
  res = []
  for counter, line in enumerate(lines):
    pass_this = pass_next
    pass_next = False
    if pass_this:
      continue
    if re.match('^;', line) or not line:
      continue
    if 'assume D' in line:
      D = int(line.split(' ')[2][:-1])
    if line == '...':
      pass_next = True
      # get the previous line, and loop
      nextline = lines[counter+1]
      fmt_string = nextline.replace('D', '{i}')
      for i in range(2, D + 1):
        res.append(fmt_string.format(i = i))
    elif '...' in line:
      symbol = line.split()[1]
      replacement = ' '.join([symbol + '_' + str(i) for i in range(2, D + 1)])
      newline = line.replace('...', replacement).replace(' ' + symbol + '_D', '')
      res.append(newline)
    else:
      res.append(line)
  res = '\n'.join(res)
  return res

def build_ripl(infile = 'regression2.vnt'):
  model = load_model(infile)
  # r = MRipl(backend = 'lite', no_ripls = 1, local_mode = True)
  r = make_lite_church_prime_ripl()
  r.load_prelude()
  _ = r.execute_program(model)
  return r

def simulate(infile = 'regression2.vnt'):
  r = build_ripl(infile)
  _ = r.forget('sigma_2')
  _ = r.assume('sigma_2', 1, label = 'sigma_2')
  _ = r.forget('w')
  _ = r.assume('w', '(vector 3 -2)', label = 'w')
  _ = r.assume('mem_unif', '(mem (lambda (i) (uniform_continuous -1 1)))')
  _ = r.assume('simulate', '(lambda (i) (list (mem_unif i) (y (vector 1 (mem_unif i)))))')
  res = {'x' : [], 'y' : []}
  for i in range(20):
    thisone = r.sample('(simulate {0})'.format(i))
    res['x'].append(thisone[0])
    res['y'].append(thisone[1])
  return pd.DataFrame(res)

def runme():
  r = build_ripl()
  _ = r.sample('sigma_2')
  data = simulate()
  for i, row in data[:5].iterrows()
    r.observe('(y (vector 1 {0}))'.format(row['x']), row['y'])
    data = r.infer('(cycle ((rejection default all) (peek w) (peek sigma_2)) 1)')




(cycle ((mh default all 1) (peek sigma_2)) 1)
