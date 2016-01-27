# Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

from nose import SkipTest
from nose.tools import eq_
import numpy as np
import numpy.linalg as la

from venture.lite.function import VentureFunction
from venture.lite.sp import SPType
from venture.test.config import broken_in
from venture.test.config import collectSamples
from venture.test.config import default_num_samples
from venture.test.config import get_ripl
from venture.test.stats import reportKnownGaussian
from venture.test.stats import reportKnownMean
from venture.test.stats import statisticalTest
import venture.lite.covariance as cov
import venture.lite.types as t
import venture.lite.value as v

def squared_exponential(a, l):
  # XXX We take a squared output factor and a length-scale, divided by
  # sqrt(2) because we had omitted a factor of 2 in the formula.
  # cov.se takes a squared length-scale.
  return cov.scale(a, cov.se(2. * l**2))

# input and output types for gp
xType = t.NumberType()
oType = t.NumberType()
xsType = t.HomogeneousArrayType(xType)
osType = t.HomogeneousArrayType(oType)

meanType = SPType([xsType], osType)
def makeConstFunc(c):
  return VentureFunction(lambda x: c*np.ones(x.shape), sp_type=meanType)

#print ripl.predict('(app zero 1)')

squaredExponentialType = SPType([xsType, xsType], osType)
def makeSquaredExponential(a, l):
  return VentureFunction(squared_exponential(a, l), sp_type=squaredExponentialType)

def prep_ripl(ripl):
  ripl.assume('app', 'apply_function')
  ripl.assume('make_const_func', VentureFunction(makeConstFunc, [xType], meanType))
  ripl.assume('make_squared_exponential', VentureFunction(makeSquaredExponential, [t.NumberType(), xType], t.AnyType("VentureFunction")))
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

  predictions = collectSamples(ripl,"pid",num_samples=default_num_samples(2))
  xs = [p[0] for p in predictions]

  return reportKnownGaussian(0, 1, xs)

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
def testHyperparameterInferenceSmoke():
  ripl = get_ripl()
  fType = t.AnyType("VentureFunction")
  ripl.assume('make_const_func', VentureFunction(makeConstFunc, [xType], meanType))
  ripl.assume('make_squared_exponential', VentureFunction(makeSquaredExponential, [t.NumberType(), xType], fType))
  ripl.execute_program("""\
  [assume mean (apply_function make_const_func 0)]
  [assume a (tag (quote hypers ) 0 (inv_gamma 2 5))]
  [assume l (tag (quote hypers ) 1 (inv_gamma 5 50))]
  [assume cov (apply_function make_squared_exponential a l)]
  [assume gp (make_gp mean cov)]
""")
  ripl.observe("(gp (array 1 2 3))", array([1.1, 2.2, 3.3]))
  ripl.infer("(mh (quote hypers) one 1)")

@broken_in('puma', "Puma does not define the gaussian process builtins")
def testGPLogscore1():
  """Is this actually a valid test? The real solution to this problem
  (and to the corresponding bug with unincorporate) is to wrap the gp
  in a mem. This could be done automatically I suppose, or better
  through a library function."""

  raise SkipTest("GP logDensity is broken for multiple samples of the same input.")

  ripl = get_ripl()
  prep_ripl(ripl)

  ripl.assume('gp', '(exactly (make_gp zero sq_exp))')
  ripl.predict('(gp (array 0 0))')
  ripl.get_global_logscore()

@broken_in('puma', "Puma does not define the gaussian process builtins")
def testGPAux():
  """Make sure the GP's aux is properly maintained.  It should be an array of
  all pairs (x,y) such that the GP has been called with input x and returned
  output y."""

  ripl = get_ripl()
  prep_ripl(ripl)

  def check_firsts(stats, firsts):
    eq_(len(stats), len(firsts))
    eq_(set([xy[0] for xy in stats]), set(firsts))

  ripl.assume('gp', '(make_gp zero sq_exp)')
  ripl.predict('(gp (array 1.0 3.0))')
  check_firsts(ripl.infer('(extract_stats gp)'), {1.0, 3.0})

  ripl.observe('(gp (array 5.0))', v.VentureArray(map(v.VentureNumber, [8.8])),
          label='obs')
  check_firsts(ripl.infer('(extract_stats gp)'), {1.0, 3.0, 5.0})

  ripl.forget('obs')
  check_firsts(ripl.infer('(extract_stats gp)'), {1.0, 3.0})
