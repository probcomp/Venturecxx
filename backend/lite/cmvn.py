from psp import DeterministicPSP, NullRequestPSP, RandomPSP, TypedPSP
from sp import SP, VentureSPRecord, SPType
import math
from scipy.special import gammaln
from value import HomogeneousArrayType, NumberType # The type names are metaprogrammed pylint: disable=no-name-in-module
import numpy as np

def logGenGamma(d,x):
  term1 = float(d * (d - 1)) / 4 * math.log(math.pi)
  term2 = sum([gammaln(float(2 * x - i) / 2) for i in range(d)])
  return term1 + term2

def mvtLogDensity(x,mu,Sigma,v):
  p = np.size(x)
  pterm1 = gammaln(float(v + p) / 2)
  nterm1 = gammaln(float(v) / 2)
  nterm2 = (float(p)/2) * math.log(v * math.pi)
  nterm3 = (float(1)/2) * np.linalg.slogdet(Sigma)[1]
  nterm4 = (float(v + p)/2) * math.log(1 + (float(1)/v) * (x - mu).T * np.linalg.inv(Sigma) * (x - mu))
  return pterm1 - (nterm1 + nterm2 + nterm3 + nterm4)

def mvtSample(mu,Sigma,N):
  # TODO at some point this code was copied from the Internet, though it has since been modified
  # enough to make search non trivial
  '''
  Output:
  Produce M samples of d-dimensional multivariate t distribution
  Input:
  mu = mean (d dimensional numpy array or scalar)
  Sigma = scale matrix (dxd numpy array)
  N = degrees of freedom
  M = # of samples to produce
  '''

  d = len(Sigma)
  g = np.tile(np.random.gamma(N/2.,2./N,1),(d,1))
  Z = np.random.multivariate_normal(np.zeros(d),Sigma,1)

  return mu + (Z.T)/np.sqrt(g)


### Collapsed Multivariate Normal
# (from Murphy, section 4.6.3.3, page 134)
# D: number of dimensions
# N: number of observations
# STotal: uncentered sum-of-squares matrix (sum_{i=1}^N x_i x_i^T)
# xTotal: the sum of the observations (sum_{i=1}^N x_i)

# TODO: I remember there being mistakes in this section (wrt dividing by N)

class CMVNSPAux(object):
  def __init__(self,d):
    self.N = 0
    self.STotal = np.mat(np.zeros((d,d)))
    self.xTotal = np.mat(np.zeros((d,1)))
    self.d = d

  def copy(self):
    aux = CMVNSPAux(self.d)
    aux.N = self.N
    aux.STotal = np.copy(self.STotal)
    aux.xTotal = np.copy(self.xTotal)
    return aux

class CMVNSP(SP):
  def __init__(self,requestPSP,outputPSP,d):
    super(CMVNSP,self).__init__(requestPSP,outputPSP)
    self.d = d
  def constructSPAux(self): return CMVNSPAux(self.d)
  def show(self,spaux): return (spaux.xTotal,spaux.STotal,spaux.N)

class MakeCMVNOutputPSP(DeterministicPSP):
  def simulate(self,args):
    (m0,k0,v0,S0) = args.operandValues
    m0 = np.mat(m0).transpose()

    d = np.size(m0)
    output = TypedPSP(CMVNOutputPSP(d,m0,k0,v0,S0), SPType([], HomogeneousArrayType(NumberType())))
    return VentureSPRecord(CMVNSP(NullRequestPSP(),output,d))

  def childrenCanAAA(self): return True

  def description(self,name):
    return "(%s m0 k0 v0 S0) -> <SP () <float array>>\n  Collapsed multivariate normal with hyperparameters m0,k0,v0,S0, where parameters are named as in (Murphy, section 4.6.3.3, page 134)." % name


class CMVNOutputPSP(RandomPSP):
  def __init__(self,d,m0,k0,v0,S0):
    self.d = d
    self.m0 = m0
    self.k0 = k0
    self.v0 = v0
    self.S0 = S0

  def updatedParams(self,spaux):
    mN = ((self.k0 * self.m0 + spaux.xTotal) / (self.k0 + spaux.N))
    kN = self.k0 + spaux.N
    vN = self.v0 + spaux.N
    SN = self.S0 + spaux.STotal + (self.k0 * self.m0 * self.m0.T) - (kN * mN * mN.T)

    return (mN,kN,vN,SN)

  def mvtParams(self,mN,kN,vN,SN):
    mArg = mN
    SArg = (float(kN + 1) / (kN * (vN - self.d + 1))) * SN
    vArg = vN - self.d + 1
    return mArg,SArg,vArg

  def simulate(self,args):
    (mN,kN,vN,SN) = self.updatedParams(args.spaux)
    params = self.mvtParams(mN,kN,vN,SN)
    x = mvtSample(*params)
    return np.squeeze(np.array(x))

  def logDensity(self,x,args):
    x = np.mat(x).reshape((self.d,1))
    (mN,kN,vN,SN) = self.updatedParams(args.spaux)
    return mvtLogDensity(x, *self.mvtParams(mN,kN,vN,SN))

  def incorporate(self,x,args):
    x = np.mat(x).reshape((self.d,1))
    args.spaux.N += 1
    args.spaux.xTotal += x
    args.spaux.STotal += x * x.T

  def unincorporate(self,x,args):
    x = np.mat(x).reshape((self.d,1))
    args.spaux.N -= 1
    args.spaux.xTotal -= x
    args.spaux.STotal -= x * x.T

  def logDensityOfCounts(self,aux):
    (mN,kN,vN,SN) = self.updatedParams(aux)
    term1 = - (aux.N * self.d * math.log(math.pi)) / 2
    term2 = logGenGamma(self.d,float(vN) / 2)
    term3 = - logGenGamma(self.d,float(self.v0) / 2)
    term4 = (float(self.v0) / 2) * np.linalg.slogdet(self.S0)[1] # first is sign
    term5 = -(float(vN) / 2) * np.linalg.slogdet(SN)[1]
    term6 = (float(self.d) / 2) * math.log(float(self.k0) / kN)
    return term1 + term2 + term3 + term4 + term5 + term6

