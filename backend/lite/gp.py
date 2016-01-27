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
import numpy as np
import numpy.linalg as la
import numpy.random as npr

from venture.lite.exception import VentureValueError
from venture.lite.function import VentureFunction
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

class GP(object):
  """An immutable GP object."""
  def __init__(self, mean, covariance, samples={}):
    self.mean = mean
    self.covariance = covariance
    self.samples = samples

  def toJSON(self):
    return self.samples

  def mean_array(self, xs):
    return self.mean(np.asarray(xs))

  def cov_matrix(self, x1s, x2s):
    return self.covariance(np.asarray(x1s), np.asarray(x2s))

  def getNormal(self, xs):
    """Returns the mean and covariance matrices at a set of input points."""
    if len(self.samples) == 0:
      mu = self.mean_array(xs)
      sigma = self.cov_matrix(xs, xs)
    else:
      x2s = self.samples.keys()
      o2s = self.samples.values()

      mu1 = self.mean_array(xs)
      mu2 = self.mean_array(x2s)
      a2 = np.array(o2s)

      sigma11 = self.cov_matrix(xs, xs)
      sigma12 = self.cov_matrix(xs, x2s)
      sigma21 = self.cov_matrix(x2s, xs)
      sigma22 = self.cov_matrix(x2s, x2s)
      mu, sigma = mvnormal.conditional(np.array(o2s), mu1, mu2,
          sigma11, sigma12, sigma21, sigma22)

    return mu, sigma

  def sample(self, *xs):
    """Sample at a (set of) point(s)."""
    mu, sigma = self.getNormal(xs)
    os = npr.multivariate_normal(mu, sigma)
    return os

  def logDensity(self, xs, os):
    """Log density of a set of samples."""
    mu, sigma = self.getNormal(xs)
    return mvnormal.logpdf(np.asarray(os).reshape(len(xs),), mu, sigma)

  def logDensityOfCounts(self):
    """Log density of the current samples."""
    if len(self.samples) == 0:
      return 0

    xs = self.samples.keys()
    os = self.samples.values()

    mu = self.mean_array(xs)
    sigma = self.cov_matrix(xs, xs)

    return mvnormal.logpdf(np.asarray(os), mu, sigma)

class GPOutputPSP(RandomPSP):
  def __init__(self, mean, covariance):
    self.mean = mean
    self.covariance = covariance

  def makeGP(self, samples):
    return GP(self.mean, self.covariance, samples)

  def simulate(self,args):
    samples = args.spaux().samples
    xs = args.operandValues()[0]
    return self.makeGP(samples).sample(*xs)

  def logDensity(self,os,args):
    samples = args.spaux().samples
    xs = args.operandValues()[0]
    return self.makeGP(samples).logDensity(xs, os)

  def logDensityOfCounts(self,aux):
    return self.makeGP(aux.samples).logDensityOfCounts()

  def incorporate(self,os,args):
    samples = args.spaux().samples
    xs = args.operandValues()[0]

    for x, o in zip(xs, os):
      samples[x] = o

  def unincorporate(self,_os,args):
    samples = args.spaux().samples
    xs = args.operandValues()[0]
    for x in xs:
      del samples[x]

class GPOutputPSP1(GPOutputPSP):
  # version of GPOutputPSP that accepts and returns scalars.

  def simulate(self,args):
    samples = args.spaux().samples
    x = args.operandValues()[0]
    return self.makeGP(samples).sample(x)[0]

  def logDensity(self,o,args):
    samples = args.spaux().samples
    x = args.operandValues()[0]
    return self.makeGP(samples).logDensity([x], [o])

  def incorporate(self,o,args):
    samples = args.spaux().samples
    x = args.operandValues()[0]
    samples[x] = o

  def unincorporate(self,_o,args):
    samples = args.spaux().samples
    x = args.operandValues()[0]
    del samples[x]

gpType = SPType([t.ArrayUnboxedType(t.NumberType())], t.ArrayUnboxedType(t.NumberType()))
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
    output = dispatching_psp([gpType, gp1Type],
                             [GPOutputPSP(mean, covariance),
                              GPOutputPSP1(mean, covariance)])
    super(GPSP, self).__init__(NullRequestPSP(),output)

  def constructSPAux(self): return GPSPAux({})
  def show(self,spaux): return GP(self.mean, self.covariance, spaux)

class MakeGPOutputPSP(DeterministicMakerAAAPSP):
  def simulate(self,args):
    (mean, covariance) = args.operandValues()
    return VentureSPRecord(GPSP(mean, covariance))

  def childrenCanAAA(self): return True

  def description(self, _name=None):
    return """Constructs a Gaussian Process with the given mean and covariance functions. Note that each application of the GP involves a matrix inversion, so when sampling at many inputs it is much more efficient to batch-query by passing a vector of input values. Wrap the GP in a mem if input points might be sampled multiple times. Global Logscore is broken with GPs, as it is with all SPs that have auxen."""

makeGPType = SPType([t.AnyType("mean function"), t.AnyType("covariance function")], gpType)
makeGPSP = SP(NullRequestPSP(), TypedPSP(MakeGPOutputPSP(), makeGPType))

registerBuiltinSP("make_gp", makeGPSP)

xType = t.NumberType()
oType = t.NumberType()
xsType = t.HomogeneousArrayType(xType)
osType = t.HomogeneousArrayType(oType)

meanType = SPType([xsType], osType)
covarianceType = SPType([xsType, xsType], osType)
functionType = t.AnyType("VentureFunction")

def _mean_maker(f, argtypes):
  return deterministic_typed(
    lambda *x: VentureFunction(f(*x), sp_type=meanType),
    argtypes, functionType)
def _cov_maker(f, argtypes):
  return deterministic_typed(
    lambda *x: VentureFunction(f(*x), sp_type=covarianceType),
    argtypes, functionType)

def mean_const(c):
  return lambda x: c*np.ones(x.shape)
registerBuiltinSP("gp_mean_const", _mean_maker(mean_const, [t.NumberType()]))
registerBuiltinSP("gp_cov_const", _cov_maker(cov.const, [t.NumberType()]))
registerBuiltinSP("gp_cov_delta", _cov_maker(cov.delta, [t.NumberType()]))
registerBuiltinSP("gp_cov_se", _cov_maker(cov.se, [t.NumberType()]))
registerBuiltinSP("gp_cov_periodic", _cov_maker(cov.periodic,
    [t.NumberType(), t.NumberType()]))
registerBuiltinSP("gp_cov_rq", _cov_maker(cov.rq,
    [t.NumberType(), t.NumberType()]))
registerBuiltinSP("gp_cov_matern", _cov_maker(cov.matern,
    [t.NumberType(), t.NumberType()]))
registerBuiltinSP("gp_cov_matern_32", _cov_maker(cov.matern_32,
    [t.NumberType()]))
registerBuiltinSP("gp_cov_matern_52", _cov_maker(cov.matern_52,
    [t.NumberType()]))
registerBuiltinSP("gp_cov_linear", _cov_maker(cov.linear, [xType]))
registerBuiltinSP("gp_cov_noise", _cov_maker(cov.noise,
    [t.NumberType(), functionType]))
registerBuiltinSP("gp_cov_scale", _cov_maker(cov.scale,
    [t.NumberType(), functionType]))
registerBuiltinSP("gp_cov_sum", _cov_maker(cov.sum,
    [functionType, functionType]))
registerBuiltinSP("gp_cov_product", _cov_maker(cov.product,
    [functionType, functionType]))
