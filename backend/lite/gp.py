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

import copy
from collections import OrderedDict

import numpy as np

from venture.lite.exception import VentureValueError
from venture.lite.function import ParamLeaf
from venture.lite.function import ParamProduct
from venture.lite.function import VentureFunction
from venture.lite.function import VentureTangentFunction
from venture.lite.function import parameter_nest
from venture.lite.psp import DeterministicMakerAAAPSP
from venture.lite.psp import NullRequestPSP
from venture.lite.psp import RandomPSP
from venture.lite.psp import TypedPSP
from venture.lite.sp import SP
from venture.lite.sp import SPAux
from venture.lite.sp import SPType
from venture.lite.sp import VentureSPRecord
from venture.lite.sp_help import dispatching_psp
from venture.lite.sp_help import deterministic_typed
from venture.lite.sp_registry import registerBuiltinSP
import venture.lite.covariance as cov
import venture.lite.mvnormal as mvnormal
import venture.lite.types as t
import venture.lite.value as v

def _gp_sample(mean, covariance, samples, xs, np_rng):
  mu, sigma = _gp_mvnormal(mean, covariance, samples, xs)
  return np_rng.multivariate_normal(mu, sigma)

def _gp_logDensity(mean, covariance, samples, xs, os):
  mu, sigma = _gp_mvnormal(mean, covariance, samples, xs)
  return mvnormal.logpdf(np.asarray(os).reshape(len(xs),), mu, sigma)

def _gp_logDensityOfData(mean, covariance, samples):
  if len(samples) == 0:
    return 0
  xs = samples.keys()
  os = samples.values()
  mu = _gp_mean(mean, xs)
  sigma = _gp_covariance(covariance, xs, xs)
  return mvnormal.logpdf(np.asarray(os), mu, sigma)

def _gp_gradientOfLogDensityOfData(mean, dmean, covariance, dcovariance,
    samples):
  if len(samples) == 0:
    return 0
  xs = np.asarray(samples.keys())
  os = np.asarray(samples.values())
  mu = mean(xs)
  dmu = dmean(xs)
  sigma = covariance(xs, xs)
  dsigma = dcovariance(xs, xs)
  d_dmu, d_dsigma = mvnormal.dlogpdf(os, mu, dmu, sigma, dsigma)
  return [
    v.VentureArrayUnboxed(d_dmu, t.NumberType()),
    v.VentureArrayUnboxed(d_dsigma, t.NumberType()),
  ]

def _gp_mvnormal(mean, covariance, samples, xs):
  if len(samples) == 0:
    mu = _gp_mean(mean, xs)
    sigma = _gp_covariance(covariance, xs, xs)
  else:
    x2s = samples.keys()
    o2s = samples.values()
    mu1 = _gp_mean(mean, xs)
    mu2 = _gp_mean(mean, x2s)
    sigma11 = _gp_covariance(covariance, xs, xs)
    sigma12 = _gp_covariance(covariance, xs, x2s)
    sigma21 = _gp_covariance(covariance, x2s, xs)
    sigma22 = _gp_covariance(covariance, x2s, x2s)
    mu, sigma = mvnormal.conditional(
      np.asarray(o2s), mu1, mu2, sigma11, sigma12, sigma21, sigma22)
  return mu, sigma

def _gp_mean(mean, xs):
  return mean(np.asarray(xs))

def _gp_covariance(covariance, x1s, x2s):
  return covariance(np.asarray(x1s), np.asarray(x2s))

class GPOutputPSP(RandomPSP):
  def __init__(self, mean, covariance):
    self.mean = mean
    self.covariance = covariance

  def simulate(self, args):
    samples = args.spaux().samples
    xs = args.operandValues()[0]
    return _gp_sample(self.mean, self.covariance, samples, xs,
                      args.np_prng())

  def logDensity(self, os, args):
    samples = args.spaux().samples
    xs = args.operandValues()[0]
    return _gp_logDensity(self.mean, self.covariance, samples, xs, os)

  def logDensityOfData(self, aux):
    return _gp_logDensityOfData(self.mean, self.covariance, aux.samples)

  def incorporate(self, os, args):
    samples = args.spaux().samples
    xs = args.operandValues()[0]

    for x, o in zip(xs, os):
      samples[tuple(x) if isinstance(x, np.ndarray) else x] = o

  def unincorporate(self, _os, args):
    samples = args.spaux().samples
    xs = args.operandValues()[0]
    for x in xs:
      del samples[tuple(x) if isinstance(x, np.ndarray) else x]

class GPOutputPSP1(GPOutputPSP):
  # version of GPOutputPSP that accepts and returns scalars.

  def simulate(self, args):
    samples = args.spaux().samples
    x = args.operandValues()[0]
    return _gp_sample(self.mean, self.covariance, samples, [x],
                      args.np_prng())[0]

  def logDensity(self, o, args):
    samples = args.spaux().samples
    x = args.operandValues()[0]
    return _gp_logDensity(self.mean, self.covariance, samples, [x], [o])

  def incorporate(self, o, args):
    samples = args.spaux().samples
    x = args.operandValues()[0]
    samples[x] = o

  def unincorporate(self, _o, args):
    samples = args.spaux().samples
    x = args.operandValues()[0]
    del samples[x]

gpType = SPType(
  [t.ArrayUnboxedType(t.NumericArrayType())],
  t.ArrayUnboxedType(t.NumberType()))

gp1Type = SPType([t.NumberType()], t.NumberType())

class GPSPAux(SPAux):

  def __init__(self, samples):
    self.samples = samples

  def copy(self):
    return GPSPAux(copy.copy(self.samples))

  def asVentureValue(self):
    def encode(xy):
      # (x,y) = xy
      # Since we are assuming the domain of the GP is numeric, the
      # following suffices:
      return v.VentureArray(map(v.VentureNumber, xy))
    return v.VentureArray([encode(xy) for xy in self.samples.items()])

class GPSP(SP):

  def __init__(self, mean, covariance):
    self.mean = mean
    self.covariance = covariance
    output = dispatching_psp(
        [gpType, gp1Type],
        [GPOutputPSP(mean, covariance), GPOutputPSP1(mean, covariance)])
    super(GPSP, self).__init__(NullRequestPSP(),output)

  def constructSPAux(self):
    return GPSPAux(OrderedDict())

  def show(self, spaux):
    return '<GP mean=%r covariance=%r>' % (self.mean, self.covariance)

class MakeGPOutputPSP(DeterministicMakerAAAPSP):

  def simulate(self, args):
    (mean, covariance) = args.operandValues()
    return VentureSPRecord(GPSP(mean, covariance))

  def gradientOfLogDensityOfData(self, aux, args):
    mean, covariance = args.operandValues()
    if not isinstance(mean, VentureTangentFunction):
      raise VentureValueError('Non-differentiable GP mean: %r' % (mean,))
    if not isinstance(covariance, VentureTangentFunction):
      raise VentureValueError('Non-differentiable GP covariance kernel: %r'
        % (covariance,))
    dmean = mean.df
    dcovariance = covariance.df
    samples = aux.samples
    return _gp_gradientOfLogDensityOfData(
      mean, dmean, covariance, dcovariance, samples)

  def childrenCanAAA(self): return True

  def description(self, _name=None):
    return 'Constructs a Gaussian Process with the given mean and covariance '\
      'functions. Note that each application of the GP involves a matrix '\
      'inversion, so when sampling at many inputs it is much more efficient '\
      'to batch-query by passing a vector of input values. Wrap the GP in a '\
      'mem if input points might be sampled multiple times. Global Logscore '\
      'is broken with GPs, as it is with all SPs that have auxen.'

makeGPType = SPType(
  [t.AnyType("mean function"), t.AnyType("covariance function")], gpType)

makeGPSP = SP(NullRequestPSP(), TypedPSP(MakeGPOutputPSP(), makeGPType))

registerBuiltinSP("make_gp", makeGPSP)

xType = t.NumericArrayType("x")
oType = t.NumericArrayType("o")
xsType = t.HomogeneousArrayType(xType)
osType = t.HomogeneousArrayType(oType)

meanType = SPType([xsType], osType)
meanFunctionType = t.AnyType
covarianceType = SPType([xsType, xsType], osType)
covarianceFunctionType = t.AnyType

def _mean_maker(f, argtypes):
  return deterministic_typed(
    lambda *x: VentureFunction(f(*x), sp_type=meanType),
    argtypes,
    meanFunctionType("mean function"),
    descr=f.__doc__)

def _mean_grad_maker(f, df, s, argtypes):
  def F(*x):
    return VentureTangentFunction(f(*x), df(*x), s(*x), sp_type=meanType)
  return deterministic_typed(
    F,
    argtypes,
    meanFunctionType("mean function"),
    sim_grad=_mean_gradientOfSimulate(F),
    descr=f.__doc__)

def _mean_gradientOfSimulate(F):
  def gradientOfSimulate(args, direction):
    return parameter_nest(F(*args).parameters, direction.getArray())
  return gradientOfSimulate

def _cov_maker(f, argtypes):
  return deterministic_typed(
    lambda *x: VentureFunction(f(*x), sp_type=covarianceType),
    argtypes,
    covarianceFunctionType("covariance kernel"),
    descr=f.__doc__)

def _cov_grad_maker(f, df, s, argtypes):
  def F(*x):
    return VentureTangentFunction(f(*x), df(*x), s(*x), sp_type=covarianceType)
  return deterministic_typed(
    F,
    argtypes,
    covarianceFunctionType("covariance kernel"),
    sim_grad=_cov_gradientOfSimulate(F),
    descr=f.__doc__)

def _cov_gradientOfSimulate(F):
  def gradientOfSimulate(args, direction):
    return parameter_nest(F(*args).parameters, direction.getArray())
  return gradientOfSimulate

def shape_reals(*x):
  return [ParamLeaf() for _ in x]
def shape_scalarkernel(n, p):
  assert isinstance(p, VentureTangentFunction)
  return [ParamLeaf(), ParamProduct(p.parameters)]
def shape_kernels(*ps):
  assert all(isinstance(p, VentureTangentFunction) for p in ps)
  return [ParamProduct(p.parameters) for p in ps]

def mean_const(c):
  "Constant mean function, everywhere equal to c."
  return lambda x: c*np.ones(x.shape[0])

def d_mean_const(c):
  return lambda x: [np.ones(x.shape[0])]

registerBuiltinSP("gp_mean_const",
  _mean_grad_maker(mean_const, d_mean_const, shape_reals, [t.NumberType("c")]))

registerBuiltinSP("gp_cov_const",
  _cov_grad_maker(cov.const, cov.d_const, shape_reals, [t.NumberType("c")]))

registerBuiltinSP("gp_cov_delta",
  _cov_maker(cov.delta, [t.NumberType("tolerance")]))

registerBuiltinSP("gp_cov_se",
  _cov_grad_maker(cov.se, cov.d_se, shape_reals, [t.NumberType("l^2")]))

registerBuiltinSP("gp_cov_periodic",
  _cov_grad_maker(
    cov.periodic, cov.d_periodic, shape_reals,
    [t.NumberType("l^2"), t.NumberType("T")]))

registerBuiltinSP("gp_cov_rq",
  _cov_maker(cov.rq, [t.NumberType("l^2"), t.NumberType("alpha")]))

registerBuiltinSP("gp_cov_matern",
  _cov_maker(cov.matern, [t.NumberType("l^2"), t.NumberType("df")]))

registerBuiltinSP("gp_cov_matern_32",
  _cov_maker(cov.matern_32, [t.NumberType("l^2")]))

registerBuiltinSP("gp_cov_matern_52",
  _cov_maker(cov.matern_52, [t.NumberType("l^2")]))

registerBuiltinSP("gp_cov_linear",
  _cov_maker(cov.linear, [xType]))

registerBuiltinSP("gp_cov_bias",
  _cov_grad_maker(
    cov.bias, cov.d_bias, shape_scalarkernel,
    [t.NumberType("s^2"), covarianceFunctionType("k")]))

registerBuiltinSP("gp_cov_scale",
  _cov_grad_maker(
    cov.scale, cov.d_scale, shape_scalarkernel,
    [t.NumberType("s^2"), covarianceFunctionType("k")]))

registerBuiltinSP("gp_cov_sum",
  _cov_grad_maker(
    cov.sum, cov.d_sum, shape_kernels,
    [covarianceFunctionType("k_a"), covarianceFunctionType("k_b")]))

registerBuiltinSP("gp_cov_product",
  _cov_grad_maker(
    cov.product, cov.d_product, shape_kernels,
    [covarianceFunctionType("k_a"), covarianceFunctionType("k_b")]))
