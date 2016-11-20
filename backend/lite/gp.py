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
from venture.lite.function import parameter_nest
from venture.lite.psp import DeterministicMakerAAAPSP
from venture.lite.psp import DeterministicPSP
from venture.lite.lkernel import SimulationAAALKernel
from venture.lite.sp_help import no_request
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
from venture.lite.utils import override
import venture.lite.covariance as cov
import venture.lite.mvnormal as mvnormal
import venture.lite.types as t
import venture.lite.value as v
import venture.value.dicts as vv

def _gp_sample(mean, covariance, samples, xs, np_rng):
  mu, sigma = _gp_mvnormal(mean, covariance, samples, xs)
  return np_rng.multivariate_normal(mu, sigma)

def _gp_logDensity(mean, covariance, samples, xs, os):
  mu, sigma = _gp_mvnormal(mean, covariance, samples, xs)
  logp = mvnormal.logpdf(np.asarray(os).reshape(len(xs),), mu, sigma) 
  # horrible hack - but necessary for structure learning:
  if np.isnan(logp):
    return float("-inf")
  return logp

def _gp_gradientOfLogDensity(mean, covariance, samples, xs, os):
  # d/do_1 log P(o_1 | Mu, Sigma, x_1, X_2, O_2),
  # d/dx_1 log P(o_1 | Mu, Sigma, x_1, X_2, O_2)
  xs1 = xs
  os1 = os
  xs2 = np.array(samples.keys())
  os2 = np.array(samples.values())

  dxs1 = []
  dos1 = []

  if samples:
    mu2 = mean.f(xs2)
    sigma22 = covariance.f(xs2, xs2)
    covf22 = mvnormal._covariance_factor(sigma22) # XXX Expose?
    alpha2 = covf22.solve(os2 - mu2)

  for x1, o1 in zip(xs1, os1):
    # Reformulate the question of d/d(x, o) log P(o | Mu, Sigma, x) as
    # d/d(o, Mu, Sigma) log P(o | Mu_*, Sigma_*).
    mu1, dmu1_dx1 = mean.df_x(x1)
    assert len(dmu1_dx1) == np.asarray(x1).reshape(-1).shape[0], \
      '%r %r %r' % (x1, dmu1_dx1, np.asarray(x1).reshape(-1).shape)
    sigma11, dsigma11_dx1 = covariance.df_x(x1, np.array([x1]))
    assert len(dsigma11_dx1) == np.asarray(x1).reshape(-1).shape[0], \
      '%r %r %r' % (x1, dsigma11_dx1, np.asarray(x1).reshape(-1).shape)
    if samples:
      sigma12, dsigma12_dx1 = covariance.df_x(x1, xs2)
      assert len(dsigma12_dx1) == np.asarray(x1).reshape(-1).shape[0], \
        '%r %r %r' % (x1, dsigma12_dx1, np.asarray(x1).reshape(-1).shape)
      sigma21 = sigma12.T
      mu_, sigma_ = mvnormal.conditional(
        os2, mu1, mu2, sigma11, sigma12, sigma21, sigma22)
      dmu_ = dmu1_dx1 + np.dot(dsigma12_dx1, alpha2)
      dsigma_ = dsigma11_dx1 - np.dot(dsigma12_dx1, covf22.solve(sigma21))
    else:
      mu_, dmu_, sigma_, dsigma_ = mu1, dmu1_dx1, sigma11, dsigma11_dx1
    do = [np.ones(1)]
    dlogp_do, dlogp_dmu, dlogp_dsigma = \
      mvnormal.dlogpdf(np.array([o1]), do, mu_, dmu_, sigma_, dsigma_)
    dxs1.append(dlogp_dmu + dlogp_dsigma)
    dos1.append(dlogp_do[0])

  return np.array(dos1), [np.array(dxs1)]

def _gp_logDensityOfData(mean, covariance, samples):
  if len(samples) == 0:
    return 0
  xs = np.asarray(samples.keys())
  os = np.asarray(samples.values())
  mu = mean.f(xs)
  sigma = covariance.f(xs, xs)
  logp =  mvnormal.logpdf(os, mu, sigma)
  # horrible hack - but necessary for structure learning:
  if np.isnan(logp):
    return float("-inf")
  return logp

def _gp_gradientOfLogDensityOfData(mean, covariance, samples):
  if len(samples) == 0:
    return 0
  xs = np.asarray(samples.keys())
  os = np.asarray(samples.values())
  dos = np.zeros(os.shape)
  mu, dmu = mean.df_theta(xs)
  sigma, dsigma = covariance.df_theta(xs, xs)
  _dlogp_dos_i, dlogp_dmu_j, dlogp_dsigma_k = \
    mvnormal.dlogpdf(os, dos, mu, dmu, sigma, dsigma)
  return [dlogp_dmu_j, dlogp_dsigma_k]

def _gp_mvnormal(mean, covariance, samples, xs):
  xs = np.asarray(xs)
  if len(samples) == 0:
    mu = mean.f(xs)
    sigma = covariance.f(xs, xs)
  else:
    x2s = np.asarray(samples.keys())
    o2s = np.asarray(samples.values())
    mu1 = mean.f(xs)
    mu2 = mean.f(x2s)
    sigma11 = covariance.f(xs, xs)
    sigma12 = covariance.f(xs, x2s)
    sigma21 = covariance.f(x2s, xs)
    sigma22 = covariance.f(x2s, x2s)
    mu, sigma = mvnormal.conditional(
      o2s, mu1, mu2, sigma11, sigma12, sigma21, sigma22)
  return mu, sigma

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

  def gradientOfLogDensity(self, os, args):
    samples = args.spaux().samples
    xs = args.operandValues()[0]
    return _gp_gradientOfLogDensity(
      self.mean, self.covariance, samples, xs, os)

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

  def gradientOfLogDensity(self, o, args):
    x = args.operandValues()
    return _gp_gradientOfLogDensity(
      self.mean, self.covariance, samples, [x], [o])

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
    samples = aux.samples
    return _gp_gradientOfLogDensityOfData(mean, covariance, samples)

  def childrenCanAAA(self): return True

  def description(self, _name=None):
    return 'Constructs a Gaussian Process with the given mean and covariance '\
      'functions. Note that each application of the GP involves a matrix '\
      'inversion, so when sampling at many inputs it is much more efficient '\
      'to batch-query by passing a vector of input values. Wrap the GP in a '\
      'mem if input points might be sampled multiple times. Global Logscore '\
      'is broken with GPs, as it is with all SPs that have auxen.'


class MeanFunction(object):
  def __init__(self, *args, **kwargs):
    raise NotImplementedError
  def __repr__(self):
    raise NotImplementedError
  @property
  def parameters(self):
    raise NotImplementedError
  def f(self, X):
    raise NotImplementedError
  def df_theta(self, X):
    raise NotImplementedError
  def df_x(self, x):
    raise NotImplementedError


class mean_const(MeanFunction):
  """Constant mean function, everywhere equal to c."""

  @override(MeanFunction)
  def __init__(self, c):
    self._c = c

  @override(MeanFunction)
  def __repr__(self):
    return 'CONST(%r)' % (self._c,)

  @property
  @override(MeanFunction)
  def parameters(self):
    return [ParamLeaf()]

  @override(MeanFunction)
  def f(self, X):
    c = self._c
    return c*np.ones(X.shape[0])

  @override(MeanFunction)
  def df_theta(self, X):
    c = self._c
    return (c*np.ones(X.shape[0]), [np.ones(X.shape[0])])

  @override(MeanFunction)
  def df_x(self, x):
    c = self._c
    d = np.asarray(x).reshape(-1).shape[0]
    return (c*np.ones(1), [np.zeros(1)]*d)


class VentureGPMeanFunction(v.VentureValue):
  def __init__(self, f):
    self._f = f
  @property
  def f(self):
    return self._f
  def asStackDict(self, trace=None):
    return vv.val('gp_mean_function', self._f)
  @staticmethod
  def fromStackDict(self, thing):
    f = thing['value']
    return VentureGPMeanFunction(f)


class GPMeanType(t.VentureType):
  def __init__(self, name=None):
    self._name = name
  def asVentureValue(self, thing):
    assert isinstance(thing, MeanFunction)
    return VentureGPMeanFunction(thing)
  def asPython(self, vthing):
    assert isinstance(vthing, VentureGPMeanFunction)
    return vthing.f
  def __contains__(self, vthing):
    return isinstance(vthing, VentureGPMeanFunction)
  def name(self):
    return self._name or '<mean>'
  def distribution(self, base, **kwargs):
    return None
  def gradient_type(self):
    return t.ArrayUnboxedType(t.NumericArrayType())


class VentureGPCovarianceKernel(v.VentureValue):
  def __init__(self, kernel):
    self._kernel = kernel
  @property
  def kernel(self):
    return self._kernel
  def asStackDict(self, trace=None):
    return vv.val('gp_covariance_kernel', self._kernel)
  @staticmethod
  def fromStackDict(self, thing):
    kernel = thing['value']
    return VentureGPCovarianceKernel(kernel)


class GPCovarianceType(t.VentureType):
  def __init__(self, name=None):
    self._name = name
  def asVentureValue(self, thing):
    assert isinstance(thing, cov.Kernel)
    return VentureGPCovarianceKernel(thing)
  def asPython(self, vthing):
    assert isinstance(vthing, VentureGPCovarianceKernel)
    return vthing.kernel
  def __contains__(self, vthing):
    return isinstance(vthing, VentureGPCovarianceKernel)
  def name(self):
    return self._name or '<covariance>'
  def distribution(self, base, **kwargs):
    return None
  def gradient_type(self):
    return t.ArrayUnboxedType(t.NumericArrayType())


makeGPType = SPType(
  [GPMeanType('mean function'), GPCovarianceType('covariance kernel')], gpType)

makeGPSP = SP(NullRequestPSP(), TypedPSP(MakeGPOutputPSP(), makeGPType))

registerBuiltinSP('make_gp', makeGPSP)

xType = t.NumericArrayType('x')
oType = t.NumberType('o')


def _mean_sp(F, argtypes):
  def mean_gradientOfSimulate(args, direction):
    return parameter_nest(F(*args).parameters, direction.getArray())
  return deterministic_typed(F, argtypes, GPMeanType(),
    sim_grad=mean_gradientOfSimulate,
    descr=F.__doc__)

def _cov_sp(F, argtypes):
  def cov_gradientOfSimulate(args, direction):
    return parameter_nest(F(*args).parameters, direction.getArray())
  return deterministic_typed(F, argtypes, GPCovarianceType(),
    sim_grad=cov_gradientOfSimulate,
    descr=F.__doc__)

class MakeMakeGPMSPOutputPSP(DeterministicPSP):
    """
    We need to say ((allocate_gpmem) f) instead of just (gpmem f) -- that is,
    we need a separate gpmem-er for each f -- because the gpmem-er's SPAux will
    be used and updated by the f_probe and f_emu that it spits out.  We need a
    separate such aux for each f.
    """
    def simulate(self, args):
        return VentureSPRecord(no_request(MakeGPMSPOutputPSP()))

class MakeGPMSPOutputPSP(DeterministicPSP):
    """"
    This class (except its simulate method) is based on DeterministicAAAMakerPSP.
    """
    def __init__(self):
        self.shared_aux = GPSPAux(OrderedDict())

    def simulate(self, args):
        f_node = args.operandNodes[0]
        prior_mean_function = args.operandValues()[1]
        prior_covariance_function = args.operandValues()[2]
        f_compute = VentureSPRecord(
                SP(GPMComputerRequestPSP(f_node), GPMComputerOutputPSP()))
        f_emu = VentureSPRecord(GPSP(prior_mean_function, prior_covariance_function))
        f_emu.spAux = self.shared_aux
        f_compute.spAux = self.shared_aux
        return v.pythonListToVentureList([f_compute, f_emu])

    def childrenCanAAA(self): return True
    def getAAALKernel(self): return GPMDeterministicMakerAAALKernel(self)

class GPMDeterministicMakerAAALKernel(SimulationAAALKernel):
    """
    This is based on DeterministicMakerAAALKernel.
    """
    def __init__(self,makerPSP): self.makerPSP = makerPSP
    def simulate(self, _trace, args):
        return self.makerPSP.simulate(args)
    def weight(self, _trace, newValue, _args):
        (_f_compute, f_emu) = newValue.asPythonList()
        answer = f_emu.sp.outputPSP.logDensityOfCounts(self.makerPSP.shared_aux)
        # print "gpmem LKernel weight = %s" % answer
        return answer

allocateGPmemSP = no_request(MakeMakeGPMSPOutputPSP())

class GPMComputerRequestPSP(DeterministicPSP):
    def __init__(self, f_node):
        self.f_node = f_node

    def simulate(self, args):
        id = str(args.operandValues())
        exp = ["gpmemmedSP"] + [["quote",val] for val in args.operandValues()]
        env = VentureEnvironment(None,["gpmemmedSP"],[self.f_node])
        return Request([ESR(id,exp,emptyAddress,env)])

# TODO Perhaps this could subclass ESRRefOutputPSP to correctly handle
# back-propagation?
class GPMComputerOutputPSP(DeterministicPSP):
    def simulate(self,args):
        assert len(args.esrNodes()) ==  1
        return args.esrValues()[0]

    def incorporate(self, value, args):
        x = args.operandValues()[0].getNumber()
        y = value.getNumber()
        args.spaux().samples[x] = y

    def unincorporate(self, value, args):
        x = args.operandValues()[0].getNumber()
        samples = args.spaux().samples
        if x in samples:
            del samples[x]

registerBuiltinSP('allocate_gpmem',allocateGPmemSP)


registerBuiltinSP('gp_mean_const',
  _mean_sp(mean_const, [oType]))


registerBuiltinSP('gp_cov_const',
  _cov_sp(cov.const, [t.NumberType('c')]))

registerBuiltinSP('gp_cov_delta',
  _cov_sp(cov.delta, [t.NumberType('t^2')]))

registerBuiltinSP('gp_cov_deltoid',
  _cov_sp(cov.deltoid, [t.NumberType('t^2'), t.NumberType('s')]))

registerBuiltinSP('gp_cov_bump',
  _cov_sp(cov.bump, [t.NumberType('t_0'), t.NumberType('t_1')]))

registerBuiltinSP('gp_cov_se',
  _cov_sp(cov.se, [t.NumberType('l^2')]))

registerBuiltinSP('gp_cov_periodic',
  _cov_sp(cov.periodic, [t.NumberType('l^2'), t.NumberType('T')]))

registerBuiltinSP('gp_cov_rq',
  _cov_sp(cov.rq, [t.NumberType('l^2'), t.NumberType('alpha')]))

registerBuiltinSP('gp_cov_matern',
  _cov_sp(cov.matern, [t.NumberType('l^2'), t.NumberType('df')]))

registerBuiltinSP('gp_cov_matern_32',
  _cov_sp(cov.matern_32, [t.NumberType('l^2')]))

registerBuiltinSP('gp_cov_matern_52',
  _cov_sp(cov.matern_52, [t.NumberType('l^2')]))

registerBuiltinSP('gp_cov_linear',
  _cov_sp(cov.linear, [xType]))

registerBuiltinSP('gp_cov_bias',
  _cov_sp(cov.bias, [t.NumberType('s^2'), GPCovarianceType('K')]))

registerBuiltinSP('gp_cov_scale',
  _cov_sp(cov.scale, [t.NumberType('s^2'), GPCovarianceType('K')]))

registerBuiltinSP('gp_cov_sum',
  _cov_sp(cov.sum, [GPCovarianceType('K'), GPCovarianceType('H')]))

registerBuiltinSP('gp_cov_product',
  _cov_sp(cov.product, [GPCovarianceType('K'), GPCovarianceType('H')]))
