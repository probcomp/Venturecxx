'''
Code to build the Gaussian funnel from Neal's "Slice Sampling" paper.
Demos with the model built here are in the similarly named iPython notebook.
'''

from venture.shortcuts import make_lite_church_prime_ripl
from scipy.stats import norm
from venture.lite.psp import RandomPSP
from venture.lite.builtin import typed_nr
import random
import venture.lite.value as v
import numpy as np
from numpy import linalg as npla
from venture import shortcuts

class GaussianFunnel(RandomPSP):
  def simulate(self, args):
    # Doesn't matter
    return random.random()

  def logDensity(self, x, args):
    # x doesn't matter, the inputs do.
    v, actual_x = self.__parse_args__(args)
    return (norm.logpdf(v, loc = 0, scale = 3) +
            (norm.logpdf(actual_x, loc = 0, scale = np.sqrt(np.exp(v)))).sum())

  def gradientOfLogDensity(self, x, args):
    # gradient with respect to x is 0
    # gradient with respect to args is what we care about
    v, actual_x = self.__parse_args__(args)
    e_v = np.exp(v)
    gradX = 0
    gradV = -v / 9.0 + (1 / (2.0 * e_v)) * (actual_x ** 2).sum()
    actual_gradX = -actual_x / e_v
    return gradX, [gradV] + actual_gradX.tolist()

  def description(self,name):
    return "The density from Neal's Gaussian Funnel" % name

  def __parse_args__(self, args):
    # pass in v as a scalar, the x's as a 9-vector
    v = args.operandValues[0]
    x = np.array(args.operandValues[1:])
    return v, x

def assemble_x(i):
  instruction = {'symbol': 'x_' + str(i),
                 'instruction': 'assume',
                 'expression': ['scope_include', ['quote', 'data'],
                                {'type': 'number', 'value': float(i)},
                                ['uniform_continuous',
                                 ['mul', {'type': 'number', 'value': -1.0}, 'x_range'],
                                 'x_range']]}
  return instruction

def force_x(i):
  instruction = {'instruction' : 'force',
                 'expression' : 'x_' + str(i),
                 'value' : {'type' : 'number', 'value' : 1.0}}
  return instruction

def initialize_funnel(ripl):
  gaussianfunnel_sp = typed_nr(GaussianFunnel(),
                               [v.NumberType()] * 10,
                               v.NumberType())
  ripl.bind_foreign_sp('gaussian_funnel', gaussianfunnel_sp)
  xs = ' '.join(['x_' + str(i) for i in range(1,10)])
  funnel = '(gaussian_funnel v {0})'.format(xs)
  ripl.assume('helper', funnel)
  return ripl

def build_funnel(backend):
  # make v and the x's
  ripl = shortcuts.backend(backend).make_church_prime_ripl()
  print ripl.backend()
  ripl.assume('v', '(scope_include (quote params) 0 (normal 0 3))')
  ripl.assume('x_range', '(* 4 (sqrt (exp v)))')
  for i in range(1, 10):
    ripl.execute_instruction(assemble_x(i))
  # enforce the funnel potential
  ripl = initialize_funnel(ripl)
  # initialize values
  ripl.force('v', 0.0)
  for i in range(1, 9):
    ripl.execute_instruction(force_x(i))
  return ripl

# being lazy here and not writing out the parsed instructions... those would be pretty messy
def make_str_args(infer_args):
  if infer_args:
    return ' ' + ' '.join(map(str, infer_args_v)) + ' '
  else:
    return ' '

def assemble_infer_cycle(infer_method, infer_args_v, infer_args_x, nupdate):
  v_cycle = '({0} (quote params) 0{1}1)'.format(infer_method, make_str_args(infer_args_v))
  x_cycle = []
  for i in range(1,10):
    x = '({0} (quote data) {1}{2}1)'.format(infer_method,
                                            str(i), make_str_args(infer_args_x))
    x_cycle.append(x)
  x_cycle = ' '.join(x_cycle)
  infer_cycle = '(cycle ({0}) {1})'.format(v_cycle + ' ' + x_cycle, nupdate)
  return infer_cycle

def assemble_infer_statement(infer_method, infer_args_v, infer_args_x, nupdate, niter):
  infer_cycle = assemble_infer_cycle(infer_method, infer_args_v, infer_args_x, nupdate)
  infer_statement = '(cycle ((plotf pcd0d v) {0}) {1})'.format(infer_cycle, niter)
  return infer_statement

def run_experiment(backend, infer_method, infer_args_v, infer_args_x, nupdate, niter):
  ripl = build_funnel(backend)
  infer_statement = assemble_infer_statement(infer_method, infer_args_v,
                                             infer_args_x, nupdate, niter)
  res = ripl.infer(infer_statement)
  return res

infer_method = 'mh'
infer_args_v = []
infer_args_x = []
nupdate = 20
niter = 10
res = run_experiment('lite', 'mh', [], [], nupdate, niter)




