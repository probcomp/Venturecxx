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

import numpy as np
import numpy.linalg as la
import numpy.random as npr
from exception import VentureValueError

# XXX Replace by scipy.stats.multivariate_normal.logpdf when we
# upgrade to scipy 0.14.
def multivariate_normal_logpdf(x, mu, sigma):
  try:
    dev = x - mu
    ans = 0
    ans += (-.5*(x-mu).transpose() * la.pinv(sigma) * (x-mu))[0, 0]
    ans += -.5*len(sigma)*np.log(2 * np.pi)
    ans += -.5*np.log(la.det(sigma))
    return ans
  except la.LinAlgError as e:
    raise VentureValueError("Bad GP covariance matrix.")

def col_vec(xs):
  return np.matrix([xs]).T

class GP(object):
  """An immutable GP object."""
  def __init__(self, mean, covariance, samples={}):
    self.mean = mean
    self.covariance = covariance
    self.samples = samples
  
  def toJSON(self):
    return self.samples
  
  def mean_array(self, xs):
    return col_vec(map(self.mean, xs))
  
  def cov_matrix(self, x1s, x2s):
    return np.matrix([[self.covariance(x1, x2) for x2 in x2s] for x1 in x1s])
  
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
      a2 = col_vec(o2s)
      
      sigma11 = self.cov_matrix(xs, xs)
      sigma12 = self.cov_matrix(xs, x2s)
      sigma21 = self.cov_matrix(x2s, xs)
      sigma22 = self.cov_matrix(x2s, x2s)
      inv22 = la.pinv(sigma22)
      
      mu = mu1 + sigma12 * (inv22 * (a2 - mu2))
      sigma = sigma11 - sigma12 * inv22 * sigma21
    
    return mu, sigma

  def sample(self, *xs):
    """Sample at a (set of) point(s)."""
    mu, sigma = self.getNormal(xs)
    os = npr.multivariate_normal(mu.A1, sigma)
    return os

  def logDensity(self, xs, os):
    """Log density of a set of samples."""
    mu, sigma = self.getNormal(xs)
    return multivariate_normal_logpdf(col_vec(os), mu, sigma)

  def logDensityOfCounts(self):
    """Log density of the current samples."""
    if len(self.samples) == 0:
      return 0
    
    xs = self.samples.keys()
    os = self.samples.values()
    
    mu = self.mean_array(xs)
    sigma = self.cov_matrix(xs, xs)
    
    return multivariate_normal_logpdf(col_vec(os), mu, sigma)
  
from psp import DeterministicPSP, NullRequestPSP, RandomPSP, TypedPSP
from sp import SP, VentureSPRecord, SPType
import value as v

class GPOutputPSP(RandomPSP):
  def __init__(self, mean, covariance):
    self.mean = mean
    self.covariance = covariance
  
  def makeGP(self, samples):
    return GP(self.mean, self.covariance, samples)
  
  def simulate(self,args):
    samples = args.spaux
    xs = args.operandValues[0]
    return self.makeGP(samples).sample(*xs)

  def logDensity(self,os,args):
    samples = args.spaux
    xs = args.operandValues[0]
    return self.makeGP(samples).logDensity(xs, os)

  def logDensityOfCounts(self,samples):
    return self.makeGP(samples).logDensityOfCounts()
  
  def incorporate(self,os,args):
    samples = args.spaux
    xs = args.operandValues[0]
    
    for x, o in zip(xs, os):
      samples[x] = o

  def unincorporate(self,_os,args):
    samples = args.spaux
    xs = args.operandValues[0]
    for x in xs:
      del samples[x]

gpType = SPType([v.ArrayUnboxedType(v.NumberType())], v.ArrayUnboxedType(v.NumberType()))

class GPSP(SP):
  def __init__(self, mean, covariance):
    self.mean = mean
    self.covariance = covariance
    output = TypedPSP(GPOutputPSP(mean, covariance), gpType)
    super(GPSP, self).__init__(NullRequestPSP(),output)

  def constructSPAux(self): return {}
  def show(self,spaux): return GP(self.mean, self.covariance, spaux)

class MakeGPOutputPSP(DeterministicPSP):
  def simulate(self,args):
    mean = args.operandValues[0]
    covariance = args.operandValues[1]

    return VentureSPRecord(GPSP(mean, covariance))

  def childrenCanAAA(self): return True

  def description(self, _name=None):
    return """Constructs a Gaussian Process with the given mean and covariance functions. Wrap the gp in a mem if input points might be sampled multiple times. Global Logscore is broken with GPs, as it is with all SPs that have auxen."""

makeGPType = SPType([v.AnyType("mean function"), v.AnyType("covariance function")], gpType)
makeGPSP = SP(NullRequestPSP(), TypedPSP(MakeGPOutputPSP(), makeGPType))

