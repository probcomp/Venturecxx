from nose import SkipTest
from venture.test.config import get_ripl, collectSamples, broken_in
from venture.test.stats import statisticalTest, reportKnownMean, reportKnownMeanVariance

import numpy as np
import numpy.linalg as la
import numpy.random as npr

def linear(x1, x2):
  return x1 * x2

def squared_exponential(a, l):
  def f(x1, x2):
    return a * np.exp(- la.norm((x1-x2)/l))
  return f

from venture.lite.function import VentureFunction
from venture.lite.sp import SPType
import venture.lite.value as v
import venture.value.dicts as d

# input and output types for gp
xType = v.NumberType()
oType = v.NumberType()

constantType = SPType([v.AnyType()], oType)
def makeConstFunc(c):
  return VentureFunction(lambda _: c, sp_type=constantType)

#print ripl.predict('(app zero 1)')

squaredExponentialType = SPType([xType, xType], oType)
def makeSquaredExponential(a, l):
  return VentureFunction(squared_exponential(a, l), sp_type=squaredExponentialType)

def prep_ripl(ripl):
  ripl.assume('app', 'apply_function')
  ripl.assume('make_const_func', VentureFunction(makeConstFunc, [xType], constantType))
  ripl.assume('make_squared_exponential', VentureFunction(makeSquaredExponential, [v.NumberType(), xType], v.AnyType("VentureFunction")))
  ripl.assume('zero', "(app make_const_func 0)")
  ripl.assume('sq_exp', "(app make_squared_exponential 1 1)")

def array(xs):
  return v.VentureArrayUnboxed(np.array(xs), xType)

@broken_in('puma', "Puma does not define the gaussian process builtins")
def testGP1():
  ripl = get_ripl()
  prep_ripl(ripl)
  
  ripl.assume('gp', '(make_gp zero sq_exp)')
  ripl.sample('(gp (array 0))')
  ripl.sample('(gp (array 1))')
  ripl.sample('(gp (array 2))')
  
@broken_in('puma', "Puma does not define the gaussian process builtins")
@statisticalTest
def testGPMean1():
  ripl = get_ripl()
  prep_ripl(ripl)
  
  ripl.assume('gp', '(make_gp zero sq_exp)')
  ripl.predict("(gp (array 0))",label="pid")

  predictions = collectSamples(ripl,"pid")
  xs = [p[0] for p in predictions]

  return reportKnownMeanVariance(0, np.exp(-1), xs)

@broken_in('puma', "Puma does not define the gaussian process builtins")
@statisticalTest
def testGPMean2():
  ripl = get_ripl()
  prep_ripl(ripl)
  
  ripl.assume('gp', '(make_gp zero sq_exp)')
  ripl.observe('(gp (array -1 1))', array([-1, 1]))
  
  ripl.predict("(gp (array 0))",label="pid")

  predictions = collectSamples(ripl,"pid")
  xs = [p[0] for p in predictions]
  
  # TODO: variance
  return reportKnownMean(0, xs)

@broken_in('puma', "Puma does not define the gaussian process builtins")
def testGPLogscore1():
  """Is this actually a valid test? The real solution to this problem
  (and to the corresponding bug with unincorporate) is to wrap the gp
  in a mem. This could be done automatically I suppose, or better
  through a library function."""
   
  raise SkipTest("GP logDensity is broken for multiple samples of the same input.")

  ripl = get_ripl()
  prep_ripl(ripl)
  
  ripl.assume('gp', '(make_gp zero sq_exp)')
  ripl.predict('(gp (array 0 0))')
  ripl.get_global_logscore()

